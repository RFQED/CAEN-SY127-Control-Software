# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'error_GUI.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(460, 148)
        Dialog.setMinimumSize(QtCore.QSize(460, 148))
        Dialog.setMaximumSize(QtCore.QSize(460, 148))
        Dialog.setSizeGripEnabled(False)
        self.Error_Buttons = QtGui.QDialogButtonBox(Dialog)
        self.Error_Buttons.setGeometry(QtCore.QRect(10, 110, 441, 32))
        self.Error_Buttons.setOrientation(QtCore.Qt.Horizontal)
        self.Error_Buttons.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.Error_Buttons.setCenterButtons(False)
        self.Error_Buttons.setObjectName(_fromUtf8("Error_Buttons"))
        self.Error_Image = QtGui.QLabel(Dialog)
        self.Error_Image.setGeometry(QtCore.QRect(-10, -20, 101, 101))
        self.Error_Image.setText(_fromUtf8(""))
        self.Error_Image.setPixmap(QtGui.QPixmap(_fromUtf8("error.png")))
        self.Error_Image.setScaledContents(True)
        self.Error_Image.setObjectName(_fromUtf8("Error_Image"))
        self.Error_Title = QtGui.QLabel(Dialog)
        self.Error_Title.setGeometry(QtCore.QRect(80, 16, 351, 41))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Sans Serif"))
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.Error_Title.setFont(font)
        self.Error_Title.setWordWrap(True)
        self.Error_Title.setObjectName(_fromUtf8("Error_Title"))
        self.Error_Message = QtGui.QLabel(Dialog)
        self.Error_Message.setGeometry(QtCore.QRect(80, 70, 351, 31))
        self.Error_Message.setTextFormat(QtCore.Qt.AutoText)
        self.Error_Message.setWordWrap(True)
        self.Error_Message.setObjectName(_fromUtf8("Error_Message"))

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.Error_Buttons, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.Error_Buttons, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "I AM ERROR.", None))
        self.Error_Title.setText(_translate("Dialog", "Error: ", None))
        self.Error_Message.setText(_translate("Dialog", "An undefined error occurred. ", None))

