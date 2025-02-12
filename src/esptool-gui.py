import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog, QTextEdit)
from PyQt6.QtSerialPort import QSerialPortInfo
from PyQt6.QtCore import QThread, pyqtSignal
import esptool
import time


class DeviceSearchWorker(QThread):
    device_found = pyqtSignal(str, str, str)  # port, description, chip_type
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, port, target_chip):
        super().__init__()
        self.port = port
        self.target_chip = target_chip.lower() if target_chip != "Any" else None

    def run(self):
        try:
            # Initialize with the command interface
            initial_baud = 115200
            esp = esptool.cmds.detect_chip(port=self.port, baud=initial_baud)
            
            if esp is None:
                raise Exception("No ESP device detected")

            chip_name = esp.get_chip_description()
            mac = esp.read_mac()
            chip_info = f"{self.port} - {chip_name} (MAC: {':'.join(['%02X' % b for b in mac])})"
            
            # Only emit if chip matches target or if target is None (Any)
            if self.target_chip is None or self.target_chip in chip_name.lower():
                self.device_found.emit(self.port, chip_info, chip_name)
                self.progress.emit(f"Found matching ESP device: {chip_info}")
            else:
                self.progress.emit(f"Found non-matching ESP device: {chip_info}")
            
            esp.disconnect()
        except Exception as e:
            self.progress.emit(f"Port {self.port} - Not an ESP device ({str(e)})")
        finally:
            self.finished.emit()


class FlashWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, port, baud_rate, bin_path, flash_args):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.bin_path = bin_path
        self.flash_args = flash_args

    def run(self):
        try:
            esp = esptool.cmds.detect_chip(port=self.port, baud=self.baud_rate)
            
            if esp is None:
                raise Exception("No ESP device detected")

            self.progress.emit(f"Detected chip: {esp.get_chip_description()}")
            esp.connect()
            
            with open(self.bin_path, 'rb') as f:
                binary_data = f.read()
            
            flash_addr = int(self.flash_args['address'], 16)
            
            self.progress.emit("Erasing flash region...")
            esp.erase_region(flash_addr, len(binary_data))
            
            self.progress.emit("Writing flash...")
            esp.write_flash(
                flash_addr,
                binary_data,
                flash_size=self.flash_args['size'].lower(),
                flash_mode=self.flash_args['mode'],
                flash_freq=self.flash_args['freq']
            )
            
            self.progress.emit("Verifying flash...")
            esp.verify_flash(
                flash_addr,
                binary_data
            )
            
            self.progress.emit("Flash operation completed successfully!")
            esp.hard_reset()
            self.finished.emit(True, "Success")
            
        except Exception as e:
            error_msg = f"Error during flashing: {str(e)}"
            self.progress.emit(error_msg)
            self.finished.emit(False, error_msg)


class ESPFlasher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32 Flasher")
        self.setGeometry(100, 100, 800, 600)
        self.flash_worker = None
        self.search_workers = []
        self.port_info = {}  # Store port info for later use
        self.chip_types = {}  # Store chip types for devices
        
        # Initialize UI
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Chip Selection
        chip_layout = QHBoxLayout()
        chip_label = QLabel("Target Chip:")
        self.chip_combo = QComboBox()
        self.chip_combo.addItems([
            "Any",
            "ESP32",
            "ESP32-S2",
            "ESP32-S3",
            "ESP32-C3",
            "ESP8266"
        ])
        chip_layout.addWidget(chip_label)
        chip_layout.addWidget(self.chip_combo)
        chip_layout.addStretch()
        layout.addLayout(chip_layout)

        # Port Selection
        port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(300)
        self.search_button = QPushButton("Search Devices")
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.search_button)
        layout.addLayout(port_layout)

        # Bin File Selection
        bin_layout = QHBoxLayout()
        self.bin_path_edit = QLineEdit()
        self.bin_browse_button = QPushButton("Browse")
        bin_layout.addWidget(self.bin_path_edit)
        bin_layout.addWidget(self.bin_browse_button)
        layout.addLayout(bin_layout)

        # Flash Parameters
        params_layout = QHBoxLayout()

        # Flash Address
        address_layout = QVBoxLayout()
        address_label = QLabel("Flash Address (0x0000):")
        self.address_edit = QLineEdit("0x0000")
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_edit)
        params_layout.addLayout(address_layout)

        # Baud Rate
        baud_layout = QVBoxLayout()
        baud_label = QLabel("Baud Rate:")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["115200", "230400", "460800", "921600"])
        self.baud_combo.setCurrentText("460800")
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo)
        params_layout.addLayout(baud_layout)

        # Flash Mode
        flash_mode_layout = QVBoxLayout()
        flash_mode_label = QLabel("Flash Mode:")
        self.flash_mode_combo = QComboBox()
        self.flash_mode_combo.addItems(["qio", "qout", "dio", "dout"])
        self.flash_mode_combo.setCurrentText("dio")
        flash_mode_layout.addWidget(flash_mode_label)
        flash_mode_layout.addWidget(self.flash_mode_combo)
        params_layout.addLayout(flash_mode_layout)

        # Flash Size
        flash_size_layout = QVBoxLayout()
        flash_size_label = QLabel("Flash Size:")
        self.flash_size_combo = QComboBox()
        self.flash_size_combo.addItems(["1MB", "2MB", "4MB", "8MB", "16MB"])
        self.flash_size_combo.setCurrentText("4MB")
        flash_size_layout.addWidget(flash_size_label)
        flash_size_layout.addWidget(self.flash_size_combo)
        params_layout.addLayout(flash_size_layout)

        # Flash Frequency
        flash_freq_layout = QVBoxLayout()
        flash_freq_label = QLabel("Flash Frequency:")
        self.flash_freq_combo = QComboBox()
        self.flash_freq_combo.addItems(["40m", "80m"])
        self.flash_freq_combo.setCurrentText("80m")
        flash_freq_layout.addWidget(flash_freq_label)
        flash_freq_layout.addWidget(self.flash_freq_combo)
        params_layout.addLayout(flash_freq_layout)

        layout.addLayout(params_layout)

        # Flash Button
        self.flash_button = QPushButton("Flash ESP32")
        layout.addWidget(self.flash_button)

        # Output Console
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # Connect signals
        self.search_button.clicked.connect(self.search_devices)
        self.bin_browse_button.clicked.connect(self.browse_bin_file)
        self.flash_button.clicked.connect(self.start_flashing)
        self.chip_combo.currentTextChanged.connect(self.on_chip_changed)

    def on_chip_changed(self, chip_type):
        """Update flash parameters based on selected chip"""
        # You could add chip-specific defaults here
        if chip_type == "ESP8266":
            self.flash_mode_combo.setCurrentText("qio")
            self.flash_freq_combo.setCurrentText("40m")
        else:
            self.flash_mode_combo.setCurrentText("dio")
            self.flash_freq_combo.setCurrentText("80m")

    def search_devices(self):
        self.search_button.setEnabled(False)
        self.port_combo.clear()
        self.port_info.clear()
        self.chip_types.clear()
        
        target_chip = self.chip_combo.currentText()
        self.output.append(f"Searching for {target_chip} devices...")
        
        # Clean up any existing workers
        for worker in self.search_workers:
            if worker.isRunning():
                worker.quit()
                worker.wait()
        self.search_workers.clear()
        
        # Start a search worker for each available port
        available_ports = QSerialPortInfo.availablePorts()
        if not available_ports:
            self.output.append("No serial ports found.")
            self.search_button.setEnabled(True)
            return

        for port_info in available_ports:
            worker = DeviceSearchWorker(port_info.portName(), target_chip)
            worker.device_found.connect(self.add_device)
            worker.progress.connect(self.update_progress)
            worker.finished.connect(lambda: self.check_search_complete())
            self.search_workers.append(worker)
            worker.start()
            time.sleep(0.1)  # Small delay between port checks to avoid USB issues

    def add_device(self, port, description, chip_type):
        self.port_info[description] = port
        self.chip_types[description] = chip_type
        self.port_combo.addItem(description)

    def check_search_complete(self):
        if all(not worker.isRunning() for worker in self.search_workers):
            self.search_button.setEnabled(True)
            self.output.append("Device search completed.")
            if self.port_combo.count() == 0:
                self.output.append("No matching ESP devices found.")

    def update_progress(self, message):
        self.output.append(message)

    def browse_bin_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Firmware File", "", "Binary Files (*.bin)")
        if file_path:
            self.bin_path_edit.setText(file_path)

    def start_flashing(self):
        if not self.port_combo.currentText():
            self.output.append("Error: No device selected!")
            return
            
        port = self.port_info[self.port_combo.currentText()]
        bin_path = self.bin_path_edit.text()
        address = self.address_edit.text()

        if not bin_path:
            self.output.append("Error: No firmware file selected!")
            return
        if not os.path.isfile(bin_path):
            self.output.append("Error: Firmware file does not exist!")
            return
        if not address.startswith("0x"):
            self.output.append("Error: Invalid flash address format!")
            return

        self.flash_button.setEnabled(False)
        self.output.append("\nStarting flashing process...")

        flash_args = {
            'address': address,
            'mode': self.flash_mode_combo.currentText(),
            'size': self.flash_size_combo.currentText(),
            'freq': self.flash_freq_combo.currentText()
        }

        self.flash_worker = FlashWorker(
            port,
            int(self.baud_combo.currentText()),
            bin_path,
            flash_args
        )
        self.flash_worker.progress.connect(self.update_progress)
        self.flash_worker.finished.connect(self.flashing_finished)
        self.flash_worker.start()

    def flashing_finished(self, success, message):
        self.flash_button.setEnabled(True)
        if success:
            self.output.append("\nFlashing completed successfully!")
        else:
            self.output.append(f"\nFlashing failed: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ESPFlasher()
    window.show()
    sys.exit(app.exec())