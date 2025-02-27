# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog, QVBoxLayout, QTextEdit
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QIcon
from typing import Tuple, List
import serial
from serial.tools import list_ports
import esptool
from esptool import __version__ as esptool_version

from ui_form import Ui_mainw

gui_version = "v0.0.47"

# Dictionary of known Espressif USB VIDs
ESPRESSIF_VIDS = {
    "10C4": "Silicon Labs CP210x",
    "303A": "Espressif USB JTAG/serial debug",
    "1A86": "QinHeng Electronics CH34x",
    "0403": "FTDI"
}

class LogHandler(QObject):
    """Enhanced handler for logging operations and status updates"""
    update_status = Signal(str, str)  # Signal: (message, status_type)
    append_log = Signal(str, str)     # Signal: (message, level)

    # Status types
    ERROR = "error"
    SUCCESS = "success"
    OPERATION = "operation"
    INFO = "info"

    # Log levels
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    def __init__(self, status_line, log_text=None):
        super().__init__()
        self.status_line = status_line
        self.log_text = log_text
        self.update_status.connect(self.handle_status_update)

        if self.log_text:
            self.append_log.connect(self.handle_log_append)

    def handle_status_update(self, message, status_type):
        self.status_line.setText(message)

        if status_type == self.ERROR:
            self.status_line.setStyleSheet("color: red !important;")
        elif status_type == self.SUCCESS:
            self.status_line.setStyleSheet("color: green !important;")
        elif status_type == self.OPERATION:
            self.status_line.setStyleSheet("color: yellow !important;")
        else:  # INFO
            self.status_line.setStyleSheet("color: white !important;")

    def handle_log_append(self, message, level):
        if not self.log_text:
            return

        color = "white"
        if level == self.ERROR:
            color = "red"
        elif level == self.WARNING:
            color = "orange"
        elif level == self.DEBUG:
            color = "gray"

        self.log_text.append(f"<span style='color: {color};'>{message}</span>")

class FlashThread(QThread):
    """Thread for handling esptool operations"""
    finished_signal = Signal(bool, str)
    progress_signal = Signal(str)

    def __init__(self, operation: str, args: List[str], parent=None):
        super().__init__(parent)
        self.operation = operation
        self.args = args

    def run(self):
        try:
            self.progress_signal.emit(f"Starting {self.operation} operation with args: {' '.join(self.args)}")
            esptool.main(self.args)
            self.finished_signal.emit(True, f"{self.operation.capitalize()} completed successfully")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class mainw(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_mainw()
        self.ui.setupUi(self)


        # Initialize status and log handler
        self.log_handler = LogHandler(self.ui.lineEdit_status, self.ui.log_text)

        self.setWindowTitle(f"ESPTool-Simple-GUI {gui_version} (esptool version: {esptool_version})")
        self.update_ports()

        # Connect button signals to slots
        self.ui.pushButton_detectDevices.clicked.connect(self.detect_chips)
        self.ui.pushButton_eraseFlash.clicked.connect(self.erase_device_flash)
        self.ui.pushButton_selectFile.clicked.connect(self.select_file)
        self.ui.pushButton_flashFirmware.clicked.connect(self.flash_firmware)


    def update_ports(self):
        """Update the list of available serial ports"""
        ports = self.list_valid_ports()
        self.ui.comboBox_detectedDevices.clear()
        if ports:
            self.ui.comboBox_detectedDevices.addItems(ports)
            self.log_handler.update_status.emit(f"Found {len(ports)} potential ESP devices", LogHandler.INFO)
        else:
            self.ui.comboBox_detectedDevices.addItem("No devices found")
            self.log_handler.update_status.emit("No devices found", LogHandler.ERROR)

        self.log_handler.append_log.emit("Port scan completed", LogHandler.INFO)

    def list_valid_ports(self) -> List[str]:
        """List all potentially valid ESP device ports"""
        valid_ports = []
        for port in list_ports.comports():
            for vid in ESPRESSIF_VIDS.keys():
                if vid in port.hwid:
                    port_desc = f"{port.device} ({ESPRESSIF_VIDS[vid] if vid in ESPRESSIF_VIDS else 'Unknown'})"
                    valid_ports.append(port_desc)
                    self.log_handler.append_log.emit(
                        f"Found port: {port.device} - {port.description} - VID:{vid}",
                        LogHandler.DEBUG
                    )
                    break
        return valid_ports

    def try_detect_chip(self, port: str, baud: int) -> Tuple[bool, str]:
        """Try to detect ESP chip on specified port with detailed error handling"""
        self.log_handler.append_log.emit(f"Attempting to detect chip on {port} at {baud} baud", LogHandler.DEBUG)
        try:
            chip = esptool.detect_chip(port=port, baud=baud, connect_mode="default_reset",
                                     trace_enabled=False, connect_attempts=2)

            chip_mac = chip.read_mac()
            chip_mac_name = ":".join(f"{b:02X}" for b in chip_mac)
            chip_string = f"{port} - {chip.CHIP_NAME} - {chip_mac_name}"

            self.log_handler.append_log.emit(
                f"Detected: {chip.CHIP_NAME} with MAC: {chip_mac_name}",
                LogHandler.INFO
            )

            chip._port.close()
            return (True, chip_string)
        except Exception as e:
            error_msg = str(e)
            self.log_handler.append_log.emit(f"Detection error: {error_msg}", LogHandler.ERROR)
            return (False, error_msg)

    def detect_chips(self):
        """Scan and detect ESP chips on available ports"""
        self.log_handler.update_status.emit("Scanning for ESP devices...", LogHandler.OPERATION)
        detected_devices = []

        # Get only the port names from the UI list
        current_ports = [port.split(" (")[0] for port in self.list_valid_ports()]

        for port in current_ports:
            self.log_handler.append_log.emit(f"Checking port {port}...", LogHandler.INFO)
            success, chipinfo = self.try_detect_chip(port, 115200)
            if success:
                detected_devices.append(chipinfo)
            else:
                # Try with a different baud rate
                self.log_handler.append_log.emit(f"Retrying with 921600 baud", LogHandler.DEBUG)
                success, chipinfo = self.try_detect_chip(port, 921600)
                if success:
                    detected_devices.append(chipinfo)

        self.ui.comboBox_detectedDevices.clear()
        if detected_devices:
            self.ui.comboBox_detectedDevices.addItems(detected_devices)
            self.log_handler.update_status.emit(f"Found {len(detected_devices)} ESP devices", LogHandler.SUCCESS)
        else:
            self.ui.comboBox_detectedDevices.addItem("No devices detected")
            self.log_handler.update_status.emit("No ESP devices detected", LogHandler.ERROR)

    def get_selected_port(self) -> str:
        """Get the selected port from the combo box"""
        current_text = self.ui.comboBox_detectedDevices.currentText()
        if not current_text or current_text in ("No devices found", "No devices detected"):
            return ""

        # Extract port from format "port - chip - mac"
        return current_text.split(" - ")[0]

    def erase_device_flash(self):
        """Handle erase flash operation"""
        port = self.get_selected_port()
        if not port:
            self.log_handler.update_status.emit("No valid device selected", LogHandler.ERROR)
            return

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Confirm Erase")
        msg_box.setText(f"Are you sure you want to erase the flash on {port}?\nThis will delete ALL data on the device.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.set_ui_enabled(False)
            self.log_handler.update_status.emit(f"ERASING FLASH ON {port}...", LogHandler.OPERATION)

            args = ["--port", port, "erase_flash"]
            self.operation_thread = FlashThread("erase", args)
            self.operation_thread.finished_signal.connect(self.operation_finished)
            self.operation_thread.progress_signal.connect(
                lambda msg: self.log_handler.append_log.emit(msg, LogHandler.INFO)
            )
            self.operation_thread.start()

    def select_file(self):
        """Handle firmware file selection"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Firmware File",
            "",  # Start in current directory
            "Binary Files (*.bin);;All Files (*)"  # File filters
        )

        if file_path:
            self.ui.lineEdit_firmwareFile.setText(file_path)
            self.log_handler.update_status.emit(f"Selected file: {file_path}", LogHandler.INFO)
            self.log_handler.append_log.emit(f"Firmware file selected: {file_path}", LogHandler.INFO)
        else:
            self.log_handler.append_log.emit("No file selected", LogHandler.INFO)

    def flash_firmware(self):
        """Handle flash firmware operation"""
        port = self.get_selected_port()
        if not port:
            self.log_handler.update_status.emit("No valid device selected", LogHandler.ERROR)
            return

        firmware_path = self.ui.lineEdit_firmwareFile.text()
        if not firmware_path:
            self.log_handler.update_status.emit("No firmware file selected", LogHandler.ERROR)
            QMessageBox.critical(self, "Error", "Please select a firmware file first!")
            return

        # Fixed flash address to 0x0 for merge_bin output
        flash_address = "0x0"

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Confirm Flash")
        msg_box.setText(f"Are you sure you want to flash:\n{firmware_path}\nto port {port}?")
        msg_box.setInformativeText("This firmware will be flashed to address 0x0 as it is a merge_bin output file.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.set_ui_enabled(False)
            self.log_handler.update_status.emit(f"FLASHING FIRMWARE TO {port}...", LogHandler.OPERATION)

            args = ["--port", port, "write_flash", flash_address, firmware_path]
            self.operation_thread = FlashThread("flash", args)
            self.operation_thread.finished_signal.connect(self.operation_finished)
            self.operation_thread.progress_signal.connect(
                lambda msg: self.log_handler.append_log.emit(msg, LogHandler.INFO)
            )
            self.operation_thread.start()

    def set_ui_enabled(self, enabled: bool):
        """Enable or disable UI elements during operations"""
        self.ui.pushButton_eraseFlash.setEnabled(enabled)
        self.ui.comboBox_detectedDevices.setEnabled(enabled)
        self.ui.pushButton_detectDevices.setEnabled(enabled)
        self.ui.pushButton_flashFirmware.setEnabled(enabled)
        self.ui.pushButton_selectFile.setEnabled(enabled)

    def operation_finished(self, success: bool, message: str):
        """Handle completion of flash or erase operations"""
        self.set_ui_enabled(True)

        if success:
            self.log_handler.update_status.emit(f"Success: {message}", LogHandler.SUCCESS)
            self.log_handler.append_log.emit(message, LogHandler.INFO)
            QMessageBox.information(self, "Success", message)
        else:
            self.log_handler.update_status.emit(f"Error: {message}", LogHandler.ERROR)
            self.log_handler.append_log.emit(f"Operation failed: {message}", LogHandler.ERROR)
            QMessageBox.critical(self, "Error", f"Operation failed!\n{message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")

    app.setWindowIcon(QIcon(":/espressif_logo_256.ico"))

    widget = mainw()
    widget.show()
    sys.exit(app.exec())
