# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QIcon
from typing import Tuple
from serial.tools import list_ports
import esptool
from esptool import __version__ as esptool_version

from ui_form import Ui_mainw

gui_version = "v0.0.46"

class StatusHandler(QObject):
    update_status = Signal(str, bool)  # Signal: (message, is_error)
    update_operation = Signal(str)     # New signal for ongoing operations

    def __init__(self, line_edit):
        super().__init__()
        self.line_edit = line_edit
        self.update_status.connect(self.handle_status_update)
        self.update_operation.connect(self.handle_operation_update)  # Connect new signal

    def handle_status_update(self, message, is_error):
        self.line_edit.setText(message)
        if is_error:
            self.line_edit.setStyleSheet("color: red !important;")
        else:
            self.line_edit.setStyleSheet("color: green !important;")

    def handle_operation_update(self, message):
        """New handler for yellow operation updates"""
        self.line_edit.setText(message)
        self.line_edit.setStyleSheet("color: yellow !important;")

class FlashThread(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, port: str, args: str, parent=None):
        super().__init__(parent)
        self.port = port
        self.args = args

    def run(self):
        try:
            esptool.main(self.args)
            self.finished_signal.emit(True, f"Flash operation on port: {self.port}")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class mainw(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_mainw()
        self.ui.setupUi(self)

        # Initialize status handler
        self.status_handler = StatusHandler(self.ui.lineEdit_status)

        self.setWindowTitle(f"ESPTool-Simple-GUI {gui_version} (esptool version: {esptool_version})")
        self.update_ports()
        self.ui.pushButton_detectDevices.clicked.connect(self.detect_chips)
        self.ui.pushButton_eraseFlash.clicked.connect(self.erase_device_flash)
        self.ui.pushButton_selectFile.clicked.connect(self.select_file)
        self.ui.pushButton_selectFile.clicked.connect(self.flash_firmware)

    def update_ports(self):
        ports = self.list_valid_ports()
        self.ui.comboBox_detectedDevices.clear()
        if ports:
            self.ui.comboBox_detectedDevices.addItems(ports)
        else:
            self.ui.comboBox_detectedDevices.addItem("No devices found")
            self.status_handler.update_status.emit("No devices found", True)

    def list_valid_ports(self):
        espressif_vids = {"10C4", "303A", "1A86", "0403"}
        return [port.device for port in list_ports.comports() if any(vid in port.hwid for vid in espressif_vids)]

    def try_detect_chip(self, port: str, baud: int) -> Tuple[bool, str]:
        try:
            chip = esptool.detect_chip(port=port, baud=baud, connect_mode="default_reset",
                                     trace_enabled=False, connect_attempts=1)
            chip_mac_name = ":".join(f"{b:02X}" for b in chip.read_mac())
            chip_string = f"{port} - {chip.CHIP_NAME} - {chip_mac_name}"
            chip._port.close()
            return (True, chip_string)
        except Exception as e:
            return (False, str(e))

    def detect_chips(self):
        self.status_handler.update_status.emit("Scanning for devices...", False)
        detected_devices = []
        ports = self.list_valid_ports()

        for port in ports:
            success, chipinfo = self.try_detect_chip(port, 115200)
            if success:
                detected_devices.append(chipinfo)
            else:
                self.status_handler.update_status.emit(f"Failed to detect chip on {port}", True)

        self.ui.comboBox_detectedDevices.clear()
        if detected_devices:
            self.ui.comboBox_detectedDevices.addItems(detected_devices)
            self.status_handler.update_status.emit(f"Found {len(detected_devices)} devices", False)
        else:
            self.ui.comboBox_detectedDevices.addItem("No devices detected")
            self.status_handler.update_status.emit("No devices detected", True)

    def erase_device_flash(self):
        current_text = self.ui.comboBox_detectedDevices.currentText()
        if not current_text or current_text in ("No devices found", "No devices detected"):
            self.status_handler.update_status.emit("No valid device selected", True)
            return

        port = current_text.split(" - ")[0]

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Confirm Erase")
        msg_box.setText("Are you sure you want to erase the flash? This will delete all data on the device.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.ui.pushButton_eraseFlash.setEnabled(False)
            self.ui.comboBox_detectedDevices.setEnabled(False)
            self.ui.pushButton_detectDevices.setEnabled(False)
            self.ui.pushButton_flashFirmware.setEnabled(False)

            # Use new operation update for yellow status
            self.status_handler.update_operation.emit(f"ERASING FLASH ON {port}...")

            args = ["--port", port, "erase_flash"]
            self.erase_thread = FlashThread(port, args)
            self.erase_thread.finished_signal.connect(self.erase_finished)
            self.erase_thread.start()

    def erase_finished(self, success: bool, message: str):
        self.ui.pushButton_eraseFlash.setEnabled(True)
        self.ui.comboBox_detectedDevices.setEnabled(True)
        self.ui.pushButton_detectDevices.setEnabled(True)
        self.ui.pushButton_flashFirmware.setEnabled(True)

        if success:
            self.status_handler.update_status.emit(f"Success: {message}", False)
            QMessageBox.information(self, "Success", "Flash erased successfully!")
        else:
            self.status_handler.update_status.emit(f"Error: {message}", True)
            QMessageBox.critical(self, "Error", f"Failed to erase flash!\n{message}")

    def select_file(self):
        """Handle file selection dialog"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Firmware File",
            "",  # Start in current directory
            "Binary Files (*.bin);;All Files (*)"  # File filters
        )

        if file_path:
            self.ui.lineEdit_firmwareFile.setText(file_path)
            self.status_handler.update_status.emit(f"Selected file: {file_path}", False)
        else:
            self.status_handler.update_status.emit("No file selected", False)

    def flash_firmware(self):
        current_text = self.ui.comboBox_detectedDevices.currentText()
        if not current_text or current_text in ("No devices found", "No devices detected"):
            self.status_handler.update_status.emit("No valid device selected", True)
            return

        port = current_text.split(" - ")[0]

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Confirm Flash")
        msg_box.setText("Are you sure you want to flash the firmware? This will overwrite all data on the device.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.ui.pushButton_eraseFlash.setEnabled(False)
            self.ui.comboBox_detectedDevices.setEnabled(False)
            self.ui.pushButton_detectDevices.setEnabled(False)
            self.ui.pushButton_flashFirmware.setEnabled(False)

            # Use new operation update for yellow status
            self.status_handler.update_operation.emit(f"Flashing firmware to: {port}...")
            firmware_path = self.ui.lineEdit_firmwareFile.text()
            if not firmware_path:
                QMessageBox.critical(self, "Error", f"Firmware file is invalid!")
            #auto write firmware to 0x0, output of merge_bin
            args = ["--port", port, "write_flash", "0x0", firmware_path]
            self.flash_thread = FlashThread(port, args)
            self.flash_thread.finished_signal.connect(self.flash_finished)
            self.flash_thread.start()

    def flash_finished(self, success: bool, message: str):
        self.ui.pushButton_eraseFlash.setEnabled(True)
        self.ui.comboBox_detectedDevices.setEnabled(True)
        self.ui.pushButton_detectDevices.setEnabled(True)
        self.ui.pushButton_flashFirmware.setEnabled(True)

        if success:
            self.status_handler.update_status.emit(f"Success: {message}", False)
            QMessageBox.information(self, "Success", "Firmware flashed successfully!")
        else:
            self.status_handler.update_status.emit(f"Error: {message}", True)
            QMessageBox.critical(self, "Error", f"Failed to flash firmware!\n{message}")


if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setStyle("fusion")

    my_icon = QIcon()
    my_icon.addFile('espressif_logo_256.ico')

    app.setWindowIcon(my_icon)

    widget = mainw()
    widget.show()
    sys.exit(app.exec())
