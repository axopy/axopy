# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'templates/oscilloscope.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Oscilloscope(object):
    def setupUi(self, Oscilloscope):
        Oscilloscope.setObjectName("Oscilloscope")
        Oscilloscope.resize(400, 300)
        self.gridLayout = QtWidgets.QGridLayout(Oscilloscope)
        self.gridLayout.setObjectName("gridLayout")
        self.graphicsLayout = OscilloscopeWidget(Oscilloscope)
        self.graphicsLayout.setObjectName("graphicsLayout")
        self.gridLayout.addWidget(self.graphicsLayout, 0, 0, 1, 1)

        self.retranslateUi(Oscilloscope)
        QtCore.QMetaObject.connectSlotsByName(Oscilloscope)

    def retranslateUi(self, Oscilloscope):
        _translate = QtCore.QCoreApplication.translate
        Oscilloscope.setWindowTitle(_translate("Oscilloscope", "Form"))

from hcibench.plugins.widgets import OscilloscopeWidget
