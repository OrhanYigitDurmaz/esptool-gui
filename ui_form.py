# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QTextEdit,
    QWidget)

class Ui_mainw(object):
    def setupUi(self, mainw):
        if not mainw.objectName():
            mainw.setObjectName(u"mainw")
        mainw.resize(460, 208)
        self.gridLayout = QGridLayout(mainw)
        self.gridLayout.setObjectName(u"gridLayout")
        self.pushButton_eraseFlash = QPushButton(mainw)
        self.pushButton_eraseFlash.setObjectName(u"pushButton_eraseFlash")

        self.gridLayout.addWidget(self.pushButton_eraseFlash, 2, 2, 1, 2)

        self.comboBox_detectedDevices = QComboBox(mainw)
        self.comboBox_detectedDevices.setObjectName(u"comboBox_detectedDevices")

        self.gridLayout.addWidget(self.comboBox_detectedDevices, 0, 1, 1, 2)

        self.label_deviceToFlash = QLabel(mainw)
        self.label_deviceToFlash.setObjectName(u"label_deviceToFlash")

        self.gridLayout.addWidget(self.label_deviceToFlash, 0, 0, 1, 1)

        self.pushButton_detectDevices = QPushButton(mainw)
        self.pushButton_detectDevices.setObjectName(u"pushButton_detectDevices")

        self.gridLayout.addWidget(self.pushButton_detectDevices, 0, 3, 1, 1)

        self.label_firmwareFile = QLabel(mainw)
        self.label_firmwareFile.setObjectName(u"label_firmwareFile")

        self.gridLayout.addWidget(self.label_firmwareFile, 1, 0, 1, 1)

        self.lineEdit_status = QLineEdit(mainw)
        self.lineEdit_status.setObjectName(u"lineEdit_status")
        self.lineEdit_status.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_status, 3, 1, 1, 3)

        self.lineEdit_firmwareFile = QLineEdit(mainw)
        self.lineEdit_firmwareFile.setObjectName(u"lineEdit_firmwareFile")

        self.gridLayout.addWidget(self.lineEdit_firmwareFile, 1, 1, 1, 1)

        self.pushButton_flashFirmware = QPushButton(mainw)
        self.pushButton_flashFirmware.setObjectName(u"pushButton_flashFirmware")

        self.gridLayout.addWidget(self.pushButton_flashFirmware, 2, 0, 1, 2)

        self.label_status = QLabel(mainw)
        self.label_status.setObjectName(u"label_status")

        self.gridLayout.addWidget(self.label_status, 3, 0, 1, 1)

        self.pushButton_selectFile = QPushButton(mainw)
        self.pushButton_selectFile.setObjectName(u"pushButton_selectFile")

        self.gridLayout.addWidget(self.pushButton_selectFile, 1, 3, 1, 1)

        self.log_text = QTextEdit(mainw)
        self.log_text.setObjectName(u"log_text")
        self.log_text.setReadOnly(True)

        self.gridLayout.addWidget(self.log_text, 4, 0, 1, 4)


        self.retranslateUi(mainw)

        QMetaObject.connectSlotsByName(mainw)
    # setupUi

    def retranslateUi(self, mainw):
        mainw.setWindowTitle(QCoreApplication.translate("mainw", u"mainw", None))
        self.pushButton_eraseFlash.setText(QCoreApplication.translate("mainw", u"Erase Flash", None))
        self.label_deviceToFlash.setText(QCoreApplication.translate("mainw", u"Device to flash", None))
        self.pushButton_detectDevices.setText(QCoreApplication.translate("mainw", u"Detect devices...", None))
        self.label_firmwareFile.setText(QCoreApplication.translate("mainw", u"Firmware File", None))
        self.pushButton_flashFirmware.setText(QCoreApplication.translate("mainw", u"Flash Firmware", None))
        self.label_status.setText(QCoreApplication.translate("mainw", u"Status:", None))
        self.pushButton_selectFile.setText(QCoreApplication.translate("mainw", u"Select File", None))
    # retranslateUi

