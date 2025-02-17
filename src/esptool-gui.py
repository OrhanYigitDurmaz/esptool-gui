import sys
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog, QTextEdit,
                             QTabWidget, QCheckBox, QScrollArea)
from PyQt6.QtSerialPort import QSerialPortInfo
from PyQt6.QtCore import QThread, pyqtSignal
import esptool

from esptool import __version__ as esptool_version

# Mapping of default flash addresses for the fixed slots per chip type.
DEFAULT_ADDRESSES = {
    "ESP32": {"App": "0x10000", "Partition Table": "0x8000", "Bootloader": "0x1000"},
    "ESP32-S2": {"App": "0x12000", "Partition Table": "0x8000", "Bootloader": "0x0000"},
    "ESP32-S3": {"App": "0x10000", "Partition Table": "0x8000", "Bootloader": "0x1000"},
    "ESP32-C3": {"App": "0x10000", "Partition Table": "0xF800", "Bootloader": "0x0000"},
    "ESP8266": {"App": "0x00000", "Partition Table": "", "Bootloader": "0x0"},
    "Any": {"App": "0x10000", "Partition Table": "0x8000", "Bootloader": "0x1000"}
}

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
            initial_baud = 115200
            esp = esptool.cmds.detect_chip(port=self.port, baud=initial_baud)
            if esp is None:
                raise Exception("No ESP device detected")
            chip_name = esp.get_chip_description()
            mac = esp.read_mac()
            chip_info = f"{self.port} - {chip_name} (MAC: {':'.join(['%02X' % b for b in mac])})"
            if self.target_chip is None or self.target_chip in chip_name.lower():
                self.device_found.emit(self.port, chip_info, chip_name)
                self.progress.emit(f"Found matching ESP device: {chip_info}")
            else:
                self.progress.emit(f"Found non-matching ESP device: {chip_info}")
            esp.disconnect()
        except Exception as e:
            self.progress.emit(f"Error on port {self.port} - Not an ESP device ({str(e)})")
        finally:
            self.finished.emit()

class FlashWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, port, baud_rate, flash_mode, flash_size, flash_freq, tasks):
        """
        tasks: a list of dicts where each dict has:
         - 'bin_path': path to the firmware file
         - 'address': flash address in hex (e.g., "0x0000")
        """
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.flash_mode = flash_mode
        self.flash_size = flash_size
        self.flash_freq = flash_freq
        self.tasks = tasks

    def run(self):
        try:
            esp = esptool.cmds.detect_chip(port=self.port, baud=self.baud_rate)
            if esp is None:
                raise Exception("No ESP device detected")
            self.progress.emit(f"Detected chip: {esp.get_chip_description()}")
            esp.connect()

            for idx, task in enumerate(self.tasks, start=1):
                bin_path = task['bin_path']
                addr_str = task['address']
                flash_addr = int(addr_str, 16)
                self.progress.emit(f"\n-- Task {idx}: Flashing file {bin_path} at address {addr_str} --")
                if not os.path.isfile(bin_path):
                    raise Exception(f"Firmware file {bin_path} does not exist!")
                with open(bin_path, 'rb') as f:
                    binary_data = f.read()
                self.progress.emit("Erasing flash region...")
                esp.erase_region(flash_addr, len(binary_data))
                self.progress.emit("Writing flash...")
                esp.write_flash(
                    flash_addr,
                    binary_data,
                    flash_size=self.flash_size.lower(),
                    flash_mode=self.flash_mode,
                    flash_freq=self.flash_freq
                )
                self.progress.emit("Verifying flash...")
                esp.verify_flash(flash_addr, binary_data)
            self.progress.emit("All flash operations completed successfully!")
            esp.hard_reset()
            self.finished.emit(True, "Success")
        except Exception as e:
            error_msg = f"Error during flashing: {str(e)}"
            self.progress.emit(error_msg)
            self.finished.emit(False, error_msg)


class ESPFlasher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESPTool GUI Version 1.0 (esptool version: " + esptool_version + ")")

        screen_geo = QApplication.primaryScreen().availableGeometry()
        sw, sh = screen_geo.width(), screen_geo.height()
        win_height = int(sh * 0.70)
        win_width = int(win_height * 1.2)
        x = (sw - win_width) // 2
        y = (sh - win_height) // 2
        self.setGeometry(x, y, win_width, win_height)

        # Workers and port information
        self.search_workers_default = []
        self.search_workers_adv = []
        self.port_info_default = {}  # {device description: port}
        self.port_info_adv = {}
        self.chip_types_default = {}
        self.chip_types_adv = {}

        self.flash_worker = None
        self.advanced_file_widgets = []  # Additional slots (deletable)

        # Advanced fixed slots dict: key is slot name and value is widget group.
        self.main_slots = {}

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create Default tab
        default_tab = QWidget()
        default_layout = QVBoxLayout(default_tab)
        self.tabs.addTab(default_tab, "Default")
        self.init_default_tab(default_layout)

        # Create Advanced tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        self.tabs.addTab(advanced_tab, "Advanced")
        self.init_advanced_tab(advanced_layout)

        # Clear Console Button added above the output console
        self.clear_console_button = QPushButton("Clear Console")
        self.clear_console_button.clicked.connect(self.clear_console)
        main_layout.addWidget(self.clear_console_button)

        # Output console (shared)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setAcceptRichText(True)
        main_layout.addWidget(self.output)

    def clear_console(self):
        self.output.clear()

    def init_default_tab(self, layout):
        # Chip Selection
        chip_layout = QHBoxLayout()
        chip_label = QLabel("Target Chip:")
        self.chip_combo_default = QComboBox()

        # Populate chip_combo_default with chip types from DEFAULT_ADDRESSES.
        # Note that each key in DEFAULT_ADDRESSES maps to a dict containing the default flash addresses
        # for each slot – for example, "ESP32" maps to {"App": "0x10000", "Partition Table": "0x8000", "Bootloader": "0x1000"}.
        chips = []
        for chip, address_info in DEFAULT_ADDRESSES.items():
            # Here, chip is the chip name (e.g., "ESP32") and address_info contains the slots' default flash addresses.
            chips.append(chip)
        self.chip_combo_default.addItems(DEFAULT_ADDRESSES.keys())
        chip_layout.addWidget(chip_label)
        chip_layout.addWidget(self.chip_combo_default)
        chip_layout.addStretch()
        layout.addLayout(chip_layout)

        # Port Selection and Search button
        port_layout = QHBoxLayout()
        self.port_combo_default = QComboBox()
        self.port_combo_default.setMinimumWidth(300)
        self.search_button_default = QPushButton("Search Devices")
        port_layout.addWidget(self.port_combo_default)
        port_layout.addWidget(self.search_button_default)
        layout.addLayout(port_layout)

        # Firmware File Selection
        file_layout = QHBoxLayout()
        self.bin_path_edit_default = QLineEdit()
        self.bin_browse_button_default = QPushButton("Browse")
        file_layout.addWidget(QLabel("Firmware File:"))
        file_layout.addWidget(self.bin_path_edit_default)
        file_layout.addWidget(self.bin_browse_button_default)
        layout.addLayout(file_layout)

        # Flash Parameters
        params_layout = QHBoxLayout()
        # Baud Rate
        baud_layout = QVBoxLayout()
        baud_label = QLabel("Baud Rate:")
        self.baud_combo_default = QComboBox()
        self.baud_combo_default.addItems(["115200", "230400", "460800", "921600"])
        self.baud_combo_default.setCurrentText("115200")
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo_default)
        params_layout.addLayout(baud_layout)
        # Flash Mode
        flash_mode_layout = QVBoxLayout()
        flash_mode_label = QLabel("Flash Mode:")
        self.flash_mode_combo_default = QComboBox()
        self.flash_mode_combo_default.addItems(["qio", "qout", "dio", "dout"])
        self.flash_mode_combo_default.setCurrentText("dio")
        flash_mode_layout.addWidget(flash_mode_label)
        flash_mode_layout.addWidget(self.flash_mode_combo_default)
        params_layout.addLayout(flash_mode_layout)
        # Flash Size
        flash_size_layout = QVBoxLayout()
        flash_size_label = QLabel("Flash Size:")
        self.flash_size_combo_default = QComboBox()
        self.flash_size_combo_default.addItems(["1MB", "2MB", "4MB", "8MB", "16MB"])
        self.flash_size_combo_default.setCurrentText("4MB")
        flash_size_layout.addWidget(flash_size_label)
        flash_size_layout.addWidget(self.flash_size_combo_default)
        params_layout.addLayout(flash_size_layout)
        # Flash Frequency
        flash_freq_layout = QVBoxLayout()
        flash_freq_label = QLabel("Flash Frequency:")
        self.flash_freq_combo_default = QComboBox()
        self.flash_freq_combo_default.addItems(["40m", "80m"])
        self.flash_freq_combo_default.setCurrentText("80m")
        flash_freq_layout.addWidget(flash_freq_label)
        flash_freq_layout.addWidget(self.flash_freq_combo_default)
        params_layout.addLayout(flash_freq_layout)

        layout.addLayout(params_layout)

        # Flash Button
        self.flash_button_default = QPushButton("Flash")
        self.chip_combo_default.currentTextChanged.connect(
            lambda chip: self.flash_button_default.setText("Flash" if chip == "Any" else "Flash " + chip)
        )
        layout.addWidget(self.flash_button_default)

        # Connect signals
        self.search_button_default.clicked.connect(self.search_devices_default)
        self.bin_browse_button_default.clicked.connect(lambda: self.browse_file(self.bin_path_edit_default))
        self.flash_button_default.clicked.connect(self.start_flashing_default)
        self.chip_combo_default.currentTextChanged.connect(lambda chip: self.on_chip_changed(chip, mode='default'))

    def init_advanced_tab(self, layout):
        # Chip Selection
        chip_layout = QHBoxLayout()
        chip_label = QLabel("Target Chip:")
        self.chip_combo_adv = QComboBox()
        self.chip_combo_adv.addItems(["Any", "ESP32", "ESP32-S2", "ESP32-S3", "ESP32-C3", "ESP8266"])
        chip_layout.addWidget(chip_label)
        chip_layout.addWidget(self.chip_combo_adv)
        chip_layout.addStretch()
        layout.addLayout(chip_layout)

        # Port selection and search button
        port_layout = QHBoxLayout()
        self.port_combo_adv = QComboBox()
        self.port_combo_adv.setMinimumWidth(300)
        self.search_button_adv = QPushButton("Search Devices")
        port_layout.addWidget(self.port_combo_adv)
        port_layout.addWidget(self.search_button_adv)
        layout.addLayout(port_layout)

        # --- Fixed Main Slots ---
        self.main_slots_container = QVBoxLayout()
        for slot_name in ["App", "Partition Table", "Bootloader"]:
            slot_layout = QHBoxLayout()
            slot_label = QLabel(slot_name + ":")
            file_edit = QLineEdit()
            browse_button = QPushButton("Browse")
            addr_edit = QLineEdit()
            # Set default address from mapping (using current chip selection)
            default_chip = self.chip_combo_adv.currentText()
            default_addr = DEFAULT_ADDRESSES.get(default_chip, DEFAULT_ADDRESSES["Any"]).get(slot_name, "")
            addr_edit.setText(default_addr)
            slot_layout.addWidget(slot_label)
            slot_layout.addWidget(file_edit)
            slot_layout.addWidget(browse_button)
            slot_layout.addWidget(QLabel("Addr:"))
            slot_layout.addWidget(addr_edit)
            self.main_slots_container.addLayout(slot_layout)
            self.main_slots[slot_name] = {
                'file_edit': file_edit,
                'browse_button': browse_button,
                'addr_edit': addr_edit,
                'layout': slot_layout  # for reference; undeletable
            }
            browse_button.clicked.connect(lambda _, edit=file_edit: self.browse_file(edit))
        layout.addLayout(self.main_slots_container)

        # --- Additional File Slots Section ---
        separator = QLabel("Additional Files:")
        layout.addWidget(separator)

        # Container for additional file slots with a scroll area in case there are many slots
        self.advanced_slots_container = QVBoxLayout()
        slots_widget = QWidget()
        slots_widget.setLayout(self.advanced_slots_container)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(slots_widget)
        layout.addWidget(scroll_area)

        add_slot_button = QPushButton("Add Slot")
        add_slot_button.clicked.connect(self.add_advanced_slot)
        layout.addWidget(add_slot_button)

        # Flash Parameters
        params_layout = QHBoxLayout()
        # Baud Rate
        baud_layout = QVBoxLayout()
        baud_label = QLabel("Baud Rate:")
        self.baud_combo_adv = QComboBox()
        self.baud_combo_adv.addItems(["115200", "230400", "460800", "921600"])
        self.baud_combo_adv.setCurrentText("115200")
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo_adv)
        params_layout.addLayout(baud_layout)
        # Flash Mode
        flash_mode_layout = QVBoxLayout()
        flash_mode_label = QLabel("Flash Mode:")
        self.flash_mode_combo_adv = QComboBox()
        self.flash_mode_combo_adv.addItems(["qio", "qout", "dio", "dout"])
        self.flash_mode_combo_adv.setCurrentText("dio")
        flash_mode_layout.addWidget(flash_mode_label)
        flash_mode_layout.addWidget(self.flash_mode_combo_adv)
        params_layout.addLayout(flash_mode_layout)
        # Flash Size
        flash_size_layout = QVBoxLayout()
        flash_size_label = QLabel("Flash Size:")
        self.flash_size_combo_adv = QComboBox()
        self.flash_size_combo_adv.addItems(["1MB", "2MB", "4MB", "8MB", "16MB"])
        self.flash_size_combo_adv.setCurrentText("4MB")
        flash_size_layout.addWidget(flash_size_label)
        flash_size_layout.addWidget(self.flash_size_combo_adv)
        params_layout.addLayout(flash_size_layout)
        # Flash Frequency
        flash_freq_layout = QVBoxLayout()
        flash_freq_label = QLabel("Flash Frequency:")
        self.flash_freq_combo_adv = QComboBox()
        self.flash_freq_combo_adv.addItems(["40m", "80m"])
        self.flash_freq_combo_adv.setCurrentText("80m")
        flash_freq_layout.addWidget(flash_freq_label)
        flash_freq_layout.addWidget(self.flash_freq_combo_adv)
        params_layout.addLayout(flash_freq_layout)
        layout.addLayout(params_layout)

        # Flash Button for Advanced tab
        self.flash_button_adv = QPushButton("Flash")
        self.chip_combo_adv.currentTextChanged.connect(
            lambda chip: self.flash_button_adv.setText("Flash" if chip == "Any" else "Flash " + chip)
        )
        layout.addWidget(self.flash_button_adv)

        # Connect signals
        self.search_button_adv.clicked.connect(self.search_devices_adv)
        self.flash_button_adv.clicked.connect(self.start_flashing_adv)
        self.chip_combo_adv.currentTextChanged.connect(lambda chip: self.on_chip_changed(chip, mode='adv'))

        # Update main slots addresses when target chip changes
        self.chip_combo_adv.currentTextChanged.connect(self.update_main_slot_addresses)

    def update_main_slot_addresses(self):
        chip = self.chip_combo_adv.currentText()
        mapping = DEFAULT_ADDRESSES.get(chip, DEFAULT_ADDRESSES["Any"])
        for slot_name, widgets in self.main_slots.items():
            default_addr = mapping.get(slot_name, "")
            widgets['addr_edit'].setText(default_addr)

    def add_advanced_slot(self):
        # Create additional slot (numbering starts after the three fixed slots)
        slot_index = len(self.advanced_file_widgets) + 4
        slot_layout = QHBoxLayout()
        enable_checkbox = QCheckBox()
        enable_checkbox.setChecked(True)
        slot_label = QLabel(f"Slot {slot_index}:")
        file_edit = QLineEdit()
        browse_button = QPushButton("Browse")
        addr_edit = QLineEdit()
        addr_edit.setPlaceholderText("Flash Address (e.g., 0x10000)")
        delete_button = QPushButton("Delete")
        slot_layout.addWidget(enable_checkbox)
        slot_layout.addWidget(slot_label)
        slot_layout.addWidget(file_edit)
        slot_layout.addWidget(browse_button)
        slot_layout.addWidget(QLabel("Addr:"))
        slot_layout.addWidget(addr_edit)
        slot_layout.addWidget(delete_button)
        self.advanced_slots_container.addLayout(slot_layout)
        widget_group = {
            'file_edit': file_edit,
            'browse_button': browse_button,
            'addr_edit': addr_edit,
            'enable_checkbox': enable_checkbox,
            'layout': slot_layout,
            'slot_label': slot_label
        }
        self.advanced_file_widgets.append(widget_group)
        browse_button.clicked.connect(lambda _, edit=file_edit: self.browse_file(edit))
        delete_button.clicked.connect(lambda _, wg=widget_group: self.remove_advanced_slot(wg))

    def remove_advanced_slot(self, widget_group):
        # Remove the slot's widgets from the layout and delete its reference
        layout = widget_group['layout']
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                layout.removeWidget(widget)
                widget.deleteLater()
        self.advanced_slots_container.removeItem(layout)
        self.advanced_file_widgets.remove(widget_group)
        # Re-number remaining additional slots
        for idx, wg in enumerate(self.advanced_file_widgets, start=4):
            wg['slot_label'].setText(f"Slot {idx}:")

    def append_message(self, message):
        lower_msg = message.lower()
        if "error" in lower_msg or "failed" in lower_msg or "exception" in lower_msg:
            color = "red"
        elif "warning" in lower_msg:
            color = "orange"
        else:
            color = "green"
        self.output.append(f'<span style="color: {color};">{message}</span>')

    def on_chip_changed(self, chip_type, mode):
        if chip_type == "ESP8266":
            if mode == 'default':
                self.flash_mode_combo_default.setCurrentText("qio")
                self.flash_freq_combo_default.setCurrentText("40m")
            else:
                self.flash_mode_combo_adv.setCurrentText("qio")
                self.flash_freq_combo_adv.setCurrentText("40m")
        else:
            if mode == 'default':
                self.flash_mode_combo_default.setCurrentText("dio")
                self.flash_freq_combo_default.setCurrentText("80m")
            else:
                self.flash_mode_combo_adv.setCurrentText("dio")
                self.flash_freq_combo_adv.setCurrentText("80m")

    def browse_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Firmware File", "", "Binary Files (*.bin)"
        )
        if file_path:
            line_edit.setText(file_path)

    def search_devices_default(self):
        self.search_button_default.setEnabled(False)
        self.port_combo_default.clear()
        self.port_info_default.clear()
        self.chip_types_default.clear()
        target_chip = self.chip_combo_default.currentText()
        self.append_message(f"Searching for {target_chip} devices (Default) ...")
        for worker in self.search_workers_default:
            if worker.isRunning():
                worker.quit()
                worker.wait()
        self.search_workers_default.clear()

        available_ports = QSerialPortInfo.availablePorts()
        if not available_ports:
            self.append_message("Error: No serial ports found.")
            self.search_button_default.setEnabled(True)
            return

        for port_info in available_ports:
            worker = DeviceSearchWorker(port_info.portName(), target_chip)
            worker.device_found.connect(self.add_device_default)
            worker.progress.connect(self.append_message)
            worker.finished.connect(lambda: self.check_search_complete('default'))
            self.search_workers_default.append(worker)
            worker.start()
            time.sleep(0.1)

    def add_device_default(self, port, description, chip_type):
        self.port_info_default[description] = port
        self.chip_types_default[description] = chip_type
        self.port_combo_default.addItem(description)

    def search_devices_adv(self):
        self.search_button_adv.setEnabled(False)
        self.port_combo_adv.clear()
        self.port_info_adv.clear()
        self.chip_types_adv.clear()
        target_chip = self.chip_combo_adv.currentText()
        self.append_message(f"Searching for {target_chip} devices (Advanced) ...")
        for worker in self.search_workers_adv:
            if worker.isRunning():
                worker.quit()
                worker.wait()
        self.search_workers_adv.clear()

        available_ports = QSerialPortInfo.availablePorts()
        if not available_ports:
            self.append_message("Error: No serial ports found.")
            self.search_button_adv.setEnabled(True)
            return

        for port_info in available_ports:
            worker = DeviceSearchWorker(port_info.portName(), target_chip)
            worker.device_found.connect(self.add_device_adv)
            worker.progress.connect(self.append_message)
            worker.finished.connect(lambda: self.check_search_complete('adv'))
            self.search_workers_adv.append(worker)
            worker.start()
            time.sleep(0.1)

    def add_device_adv(self, port, description, chip_type):
        self.port_info_adv[description] = port
        self.chip_types_adv[description] = chip_type
        self.port_combo_adv.addItem(description)

    def check_search_complete(self, mode):
        if mode == 'default':
            if all(not worker.isRunning() for worker in self.search_workers_default):
                self.search_button_default.setEnabled(True)
                self.append_message("Device search (Default) completed.")
                if self.port_combo_default.count() == 0:
                    self.append_message("Error: No matching ESP devices found (Default).")
        else:
            if all(not worker.isRunning() for worker in self.search_workers_adv):
                self.search_button_adv.setEnabled(True)
                self.append_message("Device search (Advanced) completed.")
                if self.port_combo_adv.count() == 0:
                    self.append_message("Error: No matching ESP devices found (Advanced).")

    def start_flashing_default(self):
        if not self.port_combo_default.currentText():
            self.append_message("Error: No device selected (Default)!")
            return
        port = self.port_info_default[self.port_combo_default.currentText()]
        default_bin = self.bin_path_edit_default.text().strip()
        if not default_bin:
            self.append_message("Error: No firmware file selected in the Default tab!")
            return
        tasks = [{'bin_path': default_bin, 'address': "0x0000"}]

        self.flash_button_default.setEnabled(False)
        self.append_message("\nStarting flashing process (Default)...")
        self.flash_worker = FlashWorker(
            port,
            int(self.baud_combo_default.currentText()),
            self.flash_mode_combo_default.currentText(),
            self.flash_size_combo_default.currentText(),
            self.flash_freq_combo_default.currentText(),
            tasks
        )
        self.flash_worker.progress.connect(self.append_message)
        self.flash_worker.finished.connect(self.flashing_finished_default)
        self.flash_worker.start()

    def flashing_finished_default(self, success, message):
        self.flash_button_default.setEnabled(True)
        if success:
            self.append_message("\nFlashing (Default) completed successfully!")
        else:
            self.append_message(f"\nFlashing (Default) failed: {message}")

    def start_flashing_adv(self):
        if not self.port_combo_adv.currentText():
            self.append_message("Error: No device selected (Advanced)!")
            return
        port = self.port_info_adv[self.port_combo_adv.currentText()]
        tasks = []
        # Process fixed main slots
        for slot_name in ["App", "Partition Table", "Bootloader"]:
            file_path = self.main_slots[slot_name]['file_edit'].text().strip()
            addr = self.main_slots[slot_name]['addr_edit'].text().strip()
            if not file_path:
                self.append_message(f"Error: {slot_name} file not selected!")
                return
            if not addr.startswith("0x"):
                self.append_message(f"Error: {slot_name} has invalid flash address format!")
                return
            tasks.append({'bin_path': file_path, 'address': addr})
        # Process additional slots
        for idx, widget in enumerate(self.advanced_file_widgets, start=4):
            if widget['enable_checkbox'].isChecked():
                file_path = widget['file_edit'].text().strip()
                addr = widget['addr_edit'].text().strip()
                if not file_path:
                    self.append_message(f"Error: Slot {idx} enabled but no file selected!")
                    return
                if not addr.startswith("0x"):
                    self.append_message(f"Error: Slot {idx} has invalid flash address format!")
                    return
                tasks.append({'bin_path': file_path, 'address': addr})
        self.flash_button_adv.setEnabled(False)
        self.append_message("\nStarting flashing process (Advanced)...")
        self.flash_worker = FlashWorker(
            port,
            int(self.baud_combo_adv.currentText()),
            self.flash_mode_combo_adv.currentText(),
            self.flash_size_combo_adv.currentText(),
            self.flash_freq_combo_adv.currentText(),
            tasks
        )
        self.flash_worker.progress.connect(self.append_message)
        self.flash_worker.finished.connect(self.flashing_finished_adv)
        self.flash_worker.start()

    def flashing_finished_adv(self, success, message):
        self.flash_button_adv.setEnabled(True)
        if success:
            self.append_message("\nFlashing (Advanced) completed successfully!")
        else:
            self.append_message(f"\nFlashing (Advanced) failed: {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ESPFlasher()
    window.show()
    sys.exit(app.exec())