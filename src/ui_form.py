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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QProgressBar, QPushButton,
    QSizePolicy, QTabWidget, QTextEdit, QWidget)

class Ui_MainFrame(object):
    def setupUi(self, MainFrame):
        if not MainFrame.objectName():
            MainFrame.setObjectName(u"MainFrame")
        MainFrame.resize(400, 600)
        self.gridLayout_4 = QGridLayout(MainFrame)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.textEdit_console = QTextEdit(MainFrame)
        self.textEdit_console.setObjectName(u"textEdit_console")
        self.textEdit_console.setReadOnly(True)
        self.textEdit_console.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.gridLayout_4.addWidget(self.textEdit_console, 1, 0, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pushButton_flash = QPushButton(MainFrame)
        self.pushButton_flash.setObjectName(u"pushButton_flash")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_flash.sizePolicy().hasHeightForWidth())
        self.pushButton_flash.setSizePolicy(sizePolicy)
        self.pushButton_flash.setMinimumSize(QSize(0, 80))
        font = QFont()
        font.setFamilies([u"Swis721 BlkCn BT"])
        font.setPointSize(20)
        font.setBold(True)
        self.pushButton_flash.setFont(font)
        self.pushButton_flash.setFlat(False)

        self.horizontalLayout_4.addWidget(self.pushButton_flash)

        self.pushButton_erase = QPushButton(MainFrame)
        self.pushButton_erase.setObjectName(u"pushButton_erase")
        sizePolicy.setHeightForWidth(self.pushButton_erase.sizePolicy().hasHeightForWidth())
        self.pushButton_erase.setSizePolicy(sizePolicy)
        self.pushButton_erase.setMinimumSize(QSize(0, 80))
        font1 = QFont()
        font1.setFamilies([u"Swis721 BlkCn BT"])
        font1.setPointSize(20)
        font1.setBold(True)
        font1.setStyleStrategy(QFont.PreferAntialias)
        font1.setHintingPreference(QFont.PreferFullHinting)
        self.pushButton_erase.setFont(font1)
        self.pushButton_erase.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.pushButton_erase.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.pushButton_erase.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        self.horizontalLayout_4.addWidget(self.pushButton_erase)

        self.pushButton_3 = QPushButton(MainFrame)
        self.pushButton_3.setObjectName(u"pushButton_3")
        sizePolicy.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy)
        self.pushButton_3.setMinimumSize(QSize(0, 80))
        font2 = QFont()
        font2.setBold(True)
        font2.setUnderline(True)
        font2.setStrikeOut(False)
        self.pushButton_3.setFont(font2)

        self.horizontalLayout_4.addWidget(self.pushButton_3)

        self.label_status = QLabel(MainFrame)
        self.label_status.setObjectName(u"label_status")
        sizePolicy.setHeightForWidth(self.label_status.sizePolicy().hasHeightForWidth())
        self.label_status.setSizePolicy(sizePolicy)
        self.label_status.setMinimumSize(QSize(0, 80))
        font3 = QFont()
        font3.setFamilies([u"Swis721 BlkCn BT"])
        font3.setPointSize(24)
        font3.setBold(False)
        self.label_status.setFont(font3)
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_4.addWidget(self.label_status)


        self.gridLayout_4.addLayout(self.horizontalLayout_4, 2, 0, 1, 1)

        self.tabWidget = QTabWidget(MainFrame)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy1)
        self.tabWidget.setMinimumSize(QSize(0, 0))
        self.Default_tab = QWidget()
        self.Default_tab.setObjectName(u"Default_tab")
        self.gridLayout_2 = QGridLayout(self.Default_tab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.Default_tab)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.lineEdit_file_default = QLineEdit(self.Default_tab)
        self.lineEdit_file_default.setObjectName(u"lineEdit_file_default")

        self.horizontalLayout_3.addWidget(self.lineEdit_file_default)

        self.pushButton_selectFile = QPushButton(self.Default_tab)
        self.pushButton_selectFile.setObjectName(u"pushButton_selectFile")

        self.horizontalLayout_3.addWidget(self.pushButton_selectFile)


        self.gridLayout_2.addLayout(self.horizontalLayout_3, 2, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(self.Default_tab)
        self.label_2.setObjectName(u"label_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)
        self.label_2.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_2.addWidget(self.label_2)

        self.comboBox_detectedChips = QComboBox(self.Default_tab)
        self.comboBox_detectedChips.setObjectName(u"comboBox_detectedChips")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.comboBox_detectedChips.sizePolicy().hasHeightForWidth())
        self.comboBox_detectedChips.setSizePolicy(sizePolicy3)
        self.comboBox_detectedChips.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_2.addWidget(self.comboBox_detectedChips)

        self.pushButton_detectDevices = QPushButton(self.Default_tab)
        self.pushButton_detectDevices.setObjectName(u"pushButton_detectDevices")
        sizePolicy3.setHeightForWidth(self.pushButton_detectDevices.sizePolicy().hasHeightForWidth())
        self.pushButton_detectDevices.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.pushButton_detectDevices)


        self.gridLayout_2.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.Default_tab)
        self.label.setObjectName(u"label")
        sizePolicy2.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.label)

        self.comboBox_targetChip = QComboBox(self.Default_tab)
        self.comboBox_targetChip.setObjectName(u"comboBox_targetChip")
        sizePolicy3.setHeightForWidth(self.comboBox_targetChip.sizePolicy().hasHeightForWidth())
        self.comboBox_targetChip.setSizePolicy(sizePolicy3)
        self.comboBox_targetChip.setMinimumSize(QSize(0, 0))
        self.comboBox_targetChip.setMaximumSize(QSize(60000, 16777215))
        self.comboBox_targetChip.setMaxVisibleItems(15)

        self.horizontalLayout.addWidget(self.comboBox_targetChip)

        self.pushButton_loadChipDefaults = QPushButton(self.Default_tab)
        self.pushButton_loadChipDefaults.setObjectName(u"pushButton_loadChipDefaults")
        sizePolicy.setHeightForWidth(self.pushButton_loadChipDefaults.sizePolicy().hasHeightForWidth())
        self.pushButton_loadChipDefaults.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.pushButton_loadChipDefaults)


        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_4 = QLabel(self.Default_tab)
        self.label_4.setObjectName(u"label_4")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy4)

        self.gridLayout.addWidget(self.label_4, 2, 2, 1, 1)

        self.label_7 = QLabel(self.Default_tab)
        self.label_7.setObjectName(u"label_7")
        sizePolicy4.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy4)

        self.gridLayout.addWidget(self.label_7, 2, 0, 1, 1)

        self.label_6 = QLabel(self.Default_tab)
        self.label_6.setObjectName(u"label_6")
        sizePolicy4.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy4)

        self.gridLayout.addWidget(self.label_6, 2, 1, 1, 1)

        self.label_5 = QLabel(self.Default_tab)
        self.label_5.setObjectName(u"label_5")
        sizePolicy4.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy4)

        self.gridLayout.addWidget(self.label_5, 2, 3, 1, 1)

        self.comboBox_baudRate = QComboBox(self.Default_tab)
        self.comboBox_baudRate.setObjectName(u"comboBox_baudRate")

        self.gridLayout.addWidget(self.comboBox_baudRate, 3, 0, 1, 1)

        self.comboBox_flashMode = QComboBox(self.Default_tab)
        self.comboBox_flashMode.setObjectName(u"comboBox_flashMode")

        self.gridLayout.addWidget(self.comboBox_flashMode, 3, 1, 1, 1)

        self.comboBox_flashSize = QComboBox(self.Default_tab)
        self.comboBox_flashSize.setObjectName(u"comboBox_flashSize")

        self.gridLayout.addWidget(self.comboBox_flashSize, 3, 2, 1, 1)

        self.comboBox_flashFrequency = QComboBox(self.Default_tab)
        self.comboBox_flashFrequency.setObjectName(u"comboBox_flashFrequency")

        self.gridLayout.addWidget(self.comboBox_flashFrequency, 3, 3, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout, 3, 0, 1, 1)

        self.tabWidget.addTab(self.Default_tab, "")
        self.Advanced_tab = QWidget()
        self.Advanced_tab.setObjectName(u"Advanced_tab")
        self.gridLayout_5 = QGridLayout(self.Advanced_tab)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_8 = QLabel(self.Advanced_tab)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setTextFormat(Qt.TextFormat.MarkdownText)
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_8.setOpenExternalLinks(True)
        self.label_8.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.gridLayout_3.addWidget(self.label_8, 0, 0, 1, 1)


        self.gridLayout_5.addLayout(self.gridLayout_3, 0, 0, 1, 1)

        self.tabWidget.addTab(self.Advanced_tab, "")
        self.About_tab = QWidget()
        self.About_tab.setObjectName(u"About_tab")
        self.gridLayout_6 = QGridLayout(self.About_tab)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.label_9 = QLabel(self.About_tab)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setTextFormat(Qt.TextFormat.MarkdownText)
        self.label_9.setScaledContents(True)
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_6.addWidget(self.label_9, 0, 0, 1, 1)

        self.tabWidget.addTab(self.About_tab, "")

        self.gridLayout_4.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.progressBar = QProgressBar(MainFrame)
        self.progressBar.setObjectName(u"progressBar")
        font4 = QFont()
        font4.setPointSize(10)
        font4.setBold(True)
        font4.setStrikeOut(False)
        self.progressBar.setFont(font4)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(23)
        self.progressBar.setInvertedAppearance(False)

        self.gridLayout_4.addWidget(self.progressBar, 3, 0, 1, 1)


        self.retranslateUi(MainFrame)

        self.pushButton_flash.setDefault(False)
        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainFrame)
    # setupUi

    def retranslateUi(self, MainFrame):
        MainFrame.setWindowTitle(QCoreApplication.translate("MainFrame", u"ESPTool-GUI", None))
        self.pushButton_flash.setText(QCoreApplication.translate("MainFrame", u"FLASH", None))
        self.pushButton_erase.setText(QCoreApplication.translate("MainFrame", u"ERASE", None))
        self.pushButton_3.setText(QCoreApplication.translate("MainFrame", u"IDK, SMTHNG", None))
        self.label_status.setText(QCoreApplication.translate("MainFrame", u"READY", None))
        self.label_3.setText(QCoreApplication.translate("MainFrame", u"Firmware File:", None))
        self.lineEdit_file_default.setText("")
        self.lineEdit_file_default.setPlaceholderText(QCoreApplication.translate("MainFrame", u"FLASHES TO 0x0 BY DEFAULT!!!", None))
        self.pushButton_selectFile.setText(QCoreApplication.translate("MainFrame", u"Select File", None))
        self.label_2.setText(QCoreApplication.translate("MainFrame", u"Found devices:", None))
        self.pushButton_detectDevices.setText(QCoreApplication.translate("MainFrame", u"Search for devices...", None))
        self.label.setText(QCoreApplication.translate("MainFrame", u"Target Chip:", None))
        self.pushButton_loadChipDefaults.setText(QCoreApplication.translate("MainFrame", u"Load Chip Defaults", None))
        self.label_4.setText(QCoreApplication.translate("MainFrame", u"Flash Size", None))
        self.label_7.setText(QCoreApplication.translate("MainFrame", u"Baud Rate", None))
        self.label_6.setText(QCoreApplication.translate("MainFrame", u"Flash Mode", None))
        self.label_5.setText(QCoreApplication.translate("MainFrame", u"Flash Frequency", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Default_tab), QCoreApplication.translate("MainFrame", u"Default", None))
        self.label_8.setText(QCoreApplication.translate("MainFrame", u"<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:700;\">NOT READY (YET)</span></p><p align=\"center\"><br/></p><p align=\"center\"><a href=\"https://github.com/OrhanYigitDurmaz/esptool-gui\"><span style=\" font-size:11pt; font-weight:700; text-decoration: underline; color:#007af4;\">GitHub</span></a></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Advanced_tab), QCoreApplication.translate("MainFrame", u"Advanced", None))
        self.label_9.setText(QCoreApplication.translate("MainFrame", u"<html><head/><body><p align=\"center\"><span style=\" font-weight:700;\">What to do here</span></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.About_tab), QCoreApplication.translate("MainFrame", u"About", None))
        self.progressBar.setFormat(QCoreApplication.translate("MainFrame", u"%p%", None))
    # retranslateUi

