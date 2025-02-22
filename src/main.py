# This Python file uses the following encoding: utf-8
import sys
import traceback
from functools import partial
from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, QEvent, QObject, Signal, QThread, QMutex, QTimer, QMetaObject
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox
from PySide6.QtGui import QColor
from esptool import ESPLoader, detect_chip
from serial.tools import list_ports

gui_version = "v0.1.45"

flash_sizes = ["Keep", "2MB", "4MB", "8MB", "16MB", "32MB"]
target_chips = ["Any"] + [
    "ESP32", "ESP8266", "ESP32C2", "ESP32C3 / ESP8685", "ESP32C5",
    "ESP32C6", "ESP32C61", "ESP32H2 / ESP8684", "ESP32P4",
    "ESP32S2", "ESP32S3"
]
flash_frequencies = ["Keep", "26.7m", "40m", "80m", "120m"]
baud_rates = ["Keep", "57600", "115200", "230400", "460800", "921600", "1843200", "2000000"]
flash_modes = ["Keep", "DIO", "DOUT", "FASTRD", "QIO", "QOUT"]

chip_defaults = {
    "Any": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP8266": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32C2": {
        "baud_rate": "115200",
        "flash_freq": "40m",
        "flash_mode": "QIO",
        "flash_size": "2MB"
    },
    "ESP32C3 / ESP8685": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32C5": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32C6": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32C61": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32H2 / ESP8684": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32P4": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32S2": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
    "ESP32S3": {
        "baud_rate": "115200",
        "flash_freq": "80m",
        "flash_mode": "DIO",
        "flash_size": "4MB"
    },
}


class StatusHandler:
    """Handles status colors with dynamic theme adaptation and contrast calculation."""
    THEME_COLORS = {
        "light": {
            "idle": QColor("#e0e0e0"),
            "detecting": QColor("#fff3cd"),
            "connecting": QColor("#ffe0b2"),
            "flashing": QColor("#cfe2ff"),
            "erasing": QColor("#ffe0b2"),
            "success": QColor("#d4edda"),
            "error": QColor("#f8d7da"),
            "stop": QColor("#cccccc")
        },
        "dark": {
            "idle": QColor("#4a4a4a"),
            "detecting": QColor("#423e0e"),
            "connecting": QColor("#543e12"),
            "flashing": QColor("#1c3459"),
            "erasing": QColor("#543e12"),
            "success": QColor("#1e4620"),
            "error": QColor("#4a1a1d"),
            "stop": QColor("#333333")
        }
    }

    def __init__(self, label):
        self.label = label
        self.current_status = "idle"
        self.set_status(self.current_status)

    def _is_dark_theme(self):
        """Determine if the current theme is dark based on window color lightness."""
        return QApplication.instance().palette().window().color().lightness() < 128

    @staticmethod
    def _get_contrast_text_color(bg_color):
        """Calculate contrasting text color based on background luminance."""
        luminance = bg_color.redF() * 0.2126 + bg_color.greenF() * 0.7152 + bg_color.blueF() * 0.0722
        return QColor(Qt.white if luminance < 0.5 else Qt.black)

    def set_status(self, status):
        """Update status with theme-appropriate colors and contrasting text."""
        status_key = status.lower()
        theme = "dark" if self._is_dark_theme() else "light"
        colors = self.THEME_COLORS[theme]
        bg_color = colors.get(status_key, colors["idle"])
        text_color = self._get_contrast_text_color(bg_color)

        palette = self.label.palette()
        palette.setColor(self.label.backgroundRole(), bg_color)
        palette.setColor(self.label.foregroundRole(), text_color)
        self.label.setText(status_key.upper())
        self.label.setAutoFillBackground(True)
        self.label.setPalette(palette)
        self.label.update()
        self.current_status = status_key


class ESPWorker(QObject):
    progress_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, port: str, baud: int, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud
        self.esp: Optional[ESPLoader] = None

    def connect_to_chip(self):
        """Establish connection to ESP chip using proper esptool API"""
        try:
            self.progress_signal.emit("connecting")
            print(f"Port: {self.port}, Baud: {self.baud}")
            self.esp = detect_chip(port=self.port, baud=self.baud, connect_attempts=1)
            self.esp.connect()
            return True
        except Exception as e:
            self.error_signal.emit(f"Connection failed: {str(e)}\n{traceback.format_exc()}")
            return False


class FlashWorker(ESPWorker):
    def __init__(self, port: str, baud: int, file_path: str, address: int,
                 flash_size: str, flash_mode: str, flash_freq: str):
        super().__init__(port, baud)
        self.file_path = file_path
        self.address = address
        self.flash_size = flash_size
        self.flash_mode = flash_mode
        self.flash_freq = flash_freq

    def run(self):
        if not self.connect_to_chip():
            return
        try:
            self.progress_signal.emit("flashing")
            # Convert human-readable parameters to esptool format
            flash_freq = self.flash_freq.replace('m', '') if self.flash_freq != "Keep" else None
            flash_mode = {'DIO': 'dio', 'DOUT': 'dout', 'QIO': 'qio',
                          'QOUT': 'qout'}.get(self.flash_mode, 'dio')
            # Set flash parameters
            if self.flash_size != "Keep":
                self.esp.flash_size = self.esp.parse_flash_size_arg(self.flash_size)
            if flash_freq:
                self.esp.flash_freq = flash_freq
            if flash_mode:
                self.esp.flash_mode = flash_mode
            # Write flash
            with open(self.file_path, 'rb') as f:
                self.esp.write_flash(self.address, f.read())
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(f"Flashing failed: {str(e)}\n{traceback.format_exc()}")
        finally:
            if self.esp is not None:
                try:
                    self.esp.close()
                except Exception:
                    pass


class EraseWorker(ESPWorker):
    def run(self):
        if not self.connect_to_chip():
            return
        try:
            self.progress_signal.emit("erasing")
            self.esp.erase_flash()
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(f"Erase failed: {str(e)}\n{traceback.format_exc()}")
        finally:
            if self.esp is not None:
                try:
                    self.esp.close()
                except Exception:
                    pass


class DetectWorker(QObject):
    detected_chip = Signal(str, str)  # port, chip_type
    progress = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, target_chip: str, parent=None):
        super().__init__(parent)
        self.target_chip = target_chip
        self.mutex = QMutex()
        self._cancel = False

    def get_available_ports(self) -> List[str]:
        ports = [port.device for port in list_ports.comports()]
        print(ports)
        return ports

    def try_detect_chip(self, port: str, baud: int, chip_type: str) -> Tuple[bool, str]:
        esp = None
        try:
            esp = detect_chip(port=port, baud=baud, connect_mode="default_reset", connect_attempts=1)
            esp.connect()
            chip_name = esp.get_chip_description()
            print(chip_name)
            return (True, chip_name)
        except Exception as e:
            return (False, str(e))
        finally:
            if esp is not None:
                try:
                    esp.close()
                except Exception:
                    pass

    def _emit_finished(self):
        """Helper method to emit finished signal."""
        self.finished.emit()

    def run(self):
        self.progress.emit("detecting")
        ports = self.get_available_ports()
        detected = []
        for port in ports:
            self.mutex.lock()
            cancel = self._cancel
            self.mutex.unlock()
            if cancel:
                QMetaObject.invokeMethod(self, "_emit_finished", Qt.QueuedConnection)
                return
            try:
                if self.target_chip == "Any":
                    for chip in target_chips[1:]:  # Skip "Any"
                        print(chip)
                        success, result = self.try_detect_chip(port, 115200, chip)
                        print(success)
                        if success:
                            detected.append((port, result))
                            break
                else:
                    success, result = self.try_detect_chip(port, 115200, self.target_chip)
                    if success:
                        detected.append((port, result))
            except Exception as e:
                self.error.emit(f"Detection error on {port}: {str(e)}")
        for port, chip in detected:
            print("Emitted port:" + port + " ssadsa " + chip)
            self.detected_chip.emit(port, chip)
        print(detected)
        QMetaObject.invokeMethod(self, "_emit_finished", Qt.QueuedConnection)

    def cancel(self):
        self.mutex.lock()
        self._cancel = True
        self.mutex.unlock()


from ui_form import Ui_MainFrame

class MainFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainFrame()
        self.ui.setupUi(self)
        self.status_handler = StatusHandler(self.ui.label_status)
        self.worker_thread: Optional[QThread] = None
        self.detect_worker = None
        self.detect_thread = None
        self.setup_ui()
        self.setWindowTitle(f"ESPTool-GUI {gui_version}")

    def setup_ui(self):
        """Initialize UI components and connections"""
        # Populate comboboxes
        self.ui.comboBox_flashSize.addItems(flash_sizes)
        self.ui.comboBox_targetChip.addItems(target_chips)
        self.ui.comboBox_baudRate.addItems(baud_rates)
        self.ui.comboBox_flashMode.addItems(flash_modes)
        self.ui.comboBox_flashFrequency.addItems(flash_frequencies)
        # Populate available ports in the detected chips combobox (if desired)
        ports = [port for port in list_ports.comports()]
        for port in ports:
            self.ui.comboBox_detectedChips.addItem(port.device)
        # Connect signals
        self.ui.comboBox_targetChip.currentIndexChanged.connect(self.handle_chip_selection)
        self.ui.pushButton_loadChipDefaults.clicked.connect(self.load_chip_defaults)
        self.ui.pushButton_selectFile.clicked.connect(self.select_file)
        self.ui.pushButton_flash.clicked.connect(self.start_flash)
        self.ui.pushButton_erase.clicked.connect(self.start_erase)
        self.ui.pushButton_detectDevices.clicked.connect(self.start_detection)
        self.ui.comboBox_detectedChips.currentIndexChanged.connect(self.update_port_from_detected)
        # Set initial chip defaults
        self.update_ui_for_chip(self.ui.comboBox_targetChip.currentText())

    def changeEvent(self, event):
        """Handle theme changes at runtime."""
        if event.type() == QEvent.PaletteChange:
            self.status_handler.set_status(self.status_handler.current_status)
        super().changeEvent(event)

    def handle_chip_selection(self, index):
        selected_chip = self.ui.comboBox_targetChip.currentText()
        self.update_ui_for_chip(selected_chip)

    def set_combobox_value(self, combobox, value):
        index = combobox.findText(value)
        if index != -1:
            combobox.setCurrentIndex(index)

    def update_ui_for_chip(self, chip_name):
        defaults = chip_defaults.get(chip_name, {})
        self.set_combobox_value(self.ui.comboBox_baudRate, defaults.get("baud_rate", "Keep"))
        self.set_combobox_value(self.ui.comboBox_flashFrequency, defaults.get("flash_freq", "Keep"))
        self.set_combobox_value(self.ui.comboBox_flashMode, defaults.get("flash_mode", "Keep"))
        self.set_combobox_value(self.ui.comboBox_flashSize, defaults.get("flash_size", "Keep"))
        self.status_handler.set_status("idle")

    def load_chip_defaults(self):
        self.update_ui_for_chip(self.ui.comboBox_targetChip.currentText())

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Firmware File", "", "Bin Files (*.bin);;All Files (*)"
        )
        if file_path:
            self.ui.lineEdit_file_default.setText(file_path)

    def validate_port(self, show_error=True):
        port = self.ui.comboBox_detectedChips.currentText().strip()
        if not port:
            if show_error:
                QMessageBox.critical(self, "Error", "Serial port must be specified!")
            return False
        return True

    def resolve_parameter(self, combo_box, param_name):
        value = combo_box.currentText()
        if value == "Keep":
            selected_chip = self.ui.comboBox_targetChip.currentText()
            if selected_chip == "Any":
                for chip in target_chips[1:]:
                    default = chip_defaults[chip].get(param_name)
                    if default:
                        return default
                return "Keep"
            return chip_defaults[selected_chip].get(param_name, "Keep")
        return value

    def start_flash(self):
        if not self.validate_port():
            return
        file_path = self.ui.lineEdit_file_default.text().strip()
        if not file_path:
            QMessageBox.critical(self, "Error", "Select firmware file first!")
            return
        params = {
            "port": self.ui.comboBox_detectedChips.currentText().strip(),
            "baud": int(self.resolve_parameter(self.ui.comboBox_baudRate, "baud_rate")),
            "file_path": file_path,
            "address": 0x0,
            "flash_size": self.resolve_parameter(self.ui.comboBox_flashSize, "flash_size"),
            "flash_mode": self.resolve_parameter(self.ui.comboBox_flashMode, "flash_mode"),
            "flash_freq": self.resolve_parameter(self.ui.comboBox_flashFrequency, "flash_freq")
        }
        self.run_worker(FlashWorker, params)

    def start_erase(self):
        if not self.validate_port():
            return
        params = {
            "port": self.ui.comboBox_detectedChips.currentText().strip(),
            "baud": int(self.resolve_parameter(self.ui.comboBox_baudRate, "baud_rate"))
        }
        self.run_worker(EraseWorker, params)

    def run_worker(self, worker_class, params):
        self.toggle_buttons(False)
        self.status_handler.set_status("connecting")
        self.worker_thread = QThread()
        worker = worker_class(**params)
        worker.moveToThread(self.worker_thread)
        worker.progress_signal.connect(self.handle_progress)
        worker.finished_signal.connect(self.handle_success)
        worker.error_signal.connect(self.handle_error)
        self.worker_thread.started.connect(worker.run)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def start_detection(self):
        self.ui.comboBox_detectedChips.clear()
        self.status_handler.set_status("detecting")
        self.toggle_buttons(False)
        target_chip = self.ui.comboBox_targetChip.currentText()
        self.detect_thread = QThread()
        self.detect_worker = DetectWorker(target_chip)
        self.detect_worker.moveToThread(self.detect_thread)
        self.detect_worker.detected_chip.connect(self.handle_detected_chip)
        self.detect_worker.finished.connect(self.handle_detection_finished)
        self.detect_worker.error.connect(self.handle_detection_error)
        self.detect_thread.started.connect(self.detect_worker.run)
        self.detect_thread.start()

    def handle_detected_chip(self, port: str, chip_type: str):
        self.ui.comboBox_detectedChips.addItem(f"{port} - {chip_type}")

    def handle_detection_finished(self):
        self.status_handler.set_status("idle")
        self.toggle_buttons(True)
        self.cleanup_detection()

    def handle_detection_error(self, message: str):
        QMessageBox.critical(self, "Detection Error", message)
        self.status_handler.set_status("error")
        self.cleanup_detection()

    def update_port_from_detected(self, index):
        if index >= 0:
            text = self.ui.comboBox_detectedChips.currentText()
            port = text.split(" - ")[0]
            # Update the port selection combobox to the detected port.
            self.set_combobox_value(self.ui.comboBox_detectedChips, port)

    def cleanup_detection(self):
        if self.detect_thread and self.detect_thread.isRunning():
            self.detect_worker.cancel()
            self.detect_thread.quit()
            self.detect_thread.wait()
        self.detect_thread = None
        self.detect_worker = None

    def toggle_buttons(self, enable: bool):
        self.ui.pushButton_flash.setEnabled(enable)
        self.ui.pushButton_erase.setEnabled(enable)
        self.ui.pushButton_detectDevices.setEnabled(enable)

    def handle_progress(self, message: str):
        status_map = {
            "connecting": "connecting",
            "flashing": "flashing",
            "erasing": "erasing"
        }
        self.status_handler.set_status(status_map.get(message, "idle"))

    def handle_success(self):
        self.status_handler.set_status("success")
        self.cleanup_thread()
        self.toggle_buttons(True)

    def handle_error(self, message: str):
        QMessageBox.critical(self, "Error", message)
        self.status_handler.set_status("error")
        self.cleanup_thread()
        self.toggle_buttons(True)

    def cleanup_thread(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.worker_thread = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    widget = MainFrame()
    widget.show()
    sys.exit(app.exec())
