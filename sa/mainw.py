# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QThread, Signal
from typing import Tuple
from serial.tools import list_ports
import esptool
from esptool import __version__ as esptool_version

from ui_form import Ui_mainw

gui_version = "v0.0.46"

class FlashThread(QThread):
    # Signal to indicate completion: (success: bool, message: str)
    finished_signal = Signal(bool, str)

    def __init__(self, port: str, args: str, parent=None):
        super().__init__(parent)
        self.port = port
        self.args = args

    def run(self):
        #args = ["--port", self.port, "erase_flash"]
        try:
            esptool.main(self.args)
            self.finished_signal.emit(True, f"Flash operaiton on port: {self.port}")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class mainw(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_mainw()
        self.ui.setupUi(self)

        # Set up window name
        self.setWindowTitle(f"ESPTool-Simple-GUI {gui_version} (esptool version: {esptool_version})")

        # Fill the ports
        self.update_ports()

        # Connect detect device button
        self.ui.pushButton_detectDevices.clicked.connect(self.detect_chips)
        self.ui.pushButton_eraseFlash.clicked.connect(self.erase_device_flash)

    def update_ports(self):
        """Populate the combo box with available serial ports."""
        #ports = [port.device for port in list_ports.comports()]

        ports = self.list_valid_ports()

        self.ui.comboBox_detectedDevices.clear()
        if ports:
            self.ui.comboBox_detectedDevices.addItems(ports)
        else:
            self.ui.comboBox_detectedDevices.addItem("No devices found")

    def list_valid_ports(self):
        """Return com ports that are valid according to the VID"""
            #cp2102, espressif, ch343a
        espressif_vids = {"10C4", "303A", "1A86", "0403"}

        ports = [
            port.device for port in list_ports.comports()
            if any(vid in port.hwid for vid in espressif_vids)
        ]

        return ports


    def try_detect_chip(self, port: str, baud: int) -> Tuple[bool, str]:
        """Attempts to detect an ESP chip on the given port."""
        try:
            chip = esptool.detect_chip(
                port=port,
                baud=baud,
                connect_mode="default_reset",
                trace_enabled=False,
                connect_attempts=1,
            )
            #print(chip_info)
            port_name = str(port)
            chip_name = chip.CHIP_NAME
            chip_mac_bytes = chip.read_mac()
            if chip_mac_bytes:
                chip_mac_name = ":".join(f"{b:02X}" for b in chip_mac_bytes)

            chip_string = port_name + " - " + chip_name + " - " + chip_mac_name
            chip._port.close()
            return (True, str(chip_string)) if chip_string else (False, "No chip detected.")
        except Exception as e:
            return (False, str(e))

    def detect_chips(self):
        """Detects connected ESP devices and updates the UI."""
        detected_devices = []
        ports = self.list_valid_ports()

        for port in ports:
            success, chipinfo = self.try_detect_chip(port, 115200)
            print(chipinfo)
            if success:
                detected_devices.append(chipinfo)
            else:
                print(f"Failed to detect chip on {port}")

        self.ui.comboBox_detectedDevices.clear()
        if detected_devices:
            self.ui.comboBox_detectedDevices.addItems(detected_devices)
        else:
            self.ui.comboBox_detectedDevices.addItem("No devices detected")

    def erase_device_flash(self):
        """Gets the current selected port, then erases the flash"""

        current_text = self.ui.comboBox_detectedDevices.currentText()

        if not current_text or current_text in ("No devices found", "No devices detected"):
                print("No valid device selected.")
                return

        port = current_text.split(" - ")[0]

        self.ui.pushButton_eraseFlash.setEnabled(False)

        args = ["--port", port, "erase_flash"]


        # Create and start the thread
        self.erase_thread = FlashThread(port, args)
        self.erase_thread.finished_signal.connect(self.erase_finished)
        self.erase_thread.start()

    def erase_finished(self, success: bool, message: str):
            """Called when the erase thread finishes."""
            if success:
                print(message)
            else:
                print(f"Error erasing flash: {message}")

            # Re-enable the erase button after completion
            self.ui.pushButton_eraseFlash.setEnabled(True)
            # Optionally, you might want to update the UI or notify the user here.


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    widget = mainw()
    widget.show()
    sys.exit(app.exec())
