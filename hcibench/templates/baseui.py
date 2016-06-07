# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'templates/baseui.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_BaseUI(object):
    def setupUi(self, BaseUI):
        BaseUI.setObjectName("BaseUI")
        BaseUI.setWindowModality(QtCore.Qt.NonModal)
        BaseUI.resize(1004, 652)
        BaseUI.setStyleSheet("")
        BaseUI.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QtWidgets.QWidget(BaseUI)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setStyleSheet("")
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setObjectName("tabWidget")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        BaseUI.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(BaseUI)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1004, 24))
        self.menubar.setDefaultUp(False)
        self.menubar.setNativeMenuBar(True)
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuUtilities = QtWidgets.QMenu(self.menubar)
        self.menuUtilities.setObjectName("menuUtilities")
        self.menuExperiments = QtWidgets.QMenu(self.menubar)
        self.menuExperiments.setObjectName("menuExperiments")
        BaseUI.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(BaseUI)
        self.statusbar.setObjectName("statusbar")
        BaseUI.setStatusBar(self.statusbar)
        self.actionQuit = QtWidgets.QAction(BaseUI)
        icon = QtGui.QIcon.fromTheme("application-exit")
        self.actionQuit.setIcon(icon)
        self.actionQuit.setObjectName("actionQuit")
        self.actionNew = QtWidgets.QAction(BaseUI)
        icon = QtGui.QIcon.fromTheme("document-new")
        self.actionNew.setIcon(icon)
        self.actionNew.setObjectName("actionNew")
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuUtilities.menuAction())
        self.menubar.addAction(self.menuExperiments.menuAction())

        self.retranslateUi(BaseUI)
        self.tabWidget.setCurrentIndex(-1)
        self.actionQuit.triggered.connect(BaseUI.close)
        QtCore.QMetaObject.connectSlotsByName(BaseUI)

    def retranslateUi(self, BaseUI):
        _translate = QtCore.QCoreApplication.translate
        BaseUI.setWindowTitle(_translate("BaseUI", "HCI Bench"))
        self.menuFile.setTitle(_translate("BaseUI", "&File"))
        self.menuUtilities.setTitle(_translate("BaseUI", "Utilities"))
        self.menuExperiments.setTitle(_translate("BaseUI", "Experiments"))
        self.actionQuit.setText(_translate("BaseUI", "&Quit"))
        self.actionQuit.setShortcut(_translate("BaseUI", "Ctrl+Q"))
        self.actionNew.setText(_translate("BaseUI", "&New"))
        self.actionNew.setShortcut(_translate("BaseUI", "Ctrl+N"))

