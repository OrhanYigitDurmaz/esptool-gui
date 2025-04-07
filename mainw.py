# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QIcon
from typing import Tuple, List
from serial.tools import list_ports

import esptool
from esptool import __version__ as esptool_version
from esptool.cmds import detect_chip, run_stub, read_mac

from ui_form import Ui_mainw

gui_version = "v0.0.47"

# Dictionary of known Espressif USB VIDs
ESPRESSIF_VIDS = {
    "10C4": "Silicon Labs CP210x",
    "303A": "Espressif USB JTAG/serial debug",
    "1A86": "QinHeng Electronics CH34x",
    "0403": "FTDI"
}
#helper function to convert mac from array to string
def format_mac(mac_bytes):
    """Format MAC address bytes as a string"""
    return ":".join(f"{x:02x}" for x in mac_bytes)

class mainw(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_mainw()
        self.ui.setupUi(self)

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
        else:
            self.ui.comboBox_detectedDevices.addItem("No devices found")

    def list_valid_ports(self) -> List[str]:
        """List all potentially valid ESP device ports"""
        valid_ports = []
        for port in list_ports.comports():
            for vid in ESPRESSIF_VIDS.keys():
                if vid in port.hwid:
                    port_desc = f"{port.device} ({ESPRESSIF_VIDS[vid]})"
                    valid_ports.append(port_desc)
                    break
        return valid_ports

    def try_detect_chip(self, port: str, baud: int) -> Tuple[bool, str]:
        """        Try to detect ESP chip on specified port       """
        try:
            #TODO: maybe not run it with default-reset?
            chip = detect_chip(port=port, baud=baud, connect_mode="default-reset",
                                 trace_enabled=False, connect_attempts=2)

            chip_mac_array = chip.read_mac("BASE_MAC")
            chip_mac_str = format_mac(chip_mac_array)
            print("chip mac: " + str(chip_mac_array))
            chip_string = f"{port} - {chip.CHIP_NAME} - {chip_mac_str.upper()}"
            print(chip_string)
            # Close the port
            chip._port.close()

            return (True, chip_string)
        except Exception as e:
            error_msg = str(e)

            return (False, error_msg)

    def detect_chips(self):
        """Scan and detect ESP chips on available ports"""

        detected_devices = []
        # Get only the port names from the UI list
        current_ports = [port.split(" (")[0] for port in self.list_valid_ports()]
        print(current_ports)
        for port in current_ports:
            # try detecting chip at 921600
            success, chipinfo = self.try_detect_chip(port, 921600)
            if not success:
                #if its not working, retry at 115200 baud
                success, chipinfo = self.try_detect_chip(port, 115200)
            if success:
                #if it is working, add it to the detected_devices combobox.
                detected_devices.append(chipinfo)
        self.ui.comboBox_detectedDevices.clear()
        if detected_devices:
            self.ui.comboBox_detectedDevices.addItems(detected_devices)

        else:
            self.ui.comboBox_detectedDevices.addItem("No devices detected")


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

            return
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Confirm Erase")
        msg_box.setText(f"Are you sure you want to erase the flash on {port}?\nThis will delete ALL data on the device.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.set_ui_enabled(False)
            # delete flash
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

        else:
            print("lol no file")

    def flash_firmware(self):
        """Handle flash firmware operation"""
        port = self.get_selected_port()
        if not port:

            return
        firmware_path = self.ui.lineEdit_firmwareFile.text()
        if not firmware_path:

            QMessageBox.critical(self, "Error", "Please select a firmware file first!")
            return

        # flash fw

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
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", f"Operation failed!\n{message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    # Load the QSS file for styling
    with open("DarkPurple.qss", "r") as filer:
        app.setStyleSheet(filer.read())
    app.setWindowIcon(QIcon("./espressif_logo_256.ico"))
    widget = mainw()
    widget.show()
    sys.exit(app.exec())
