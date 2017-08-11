import sys
from PyQt5 import QtCore, QtWidgets
from axopy import util
from axopy.messaging import transmitter

key_map = {
    QtCore.Qt.Key_A: util.key_a,
    QtCore.Qt.Key_B: util.key_b,
    QtCore.Qt.Key_C: util.key_c,
    QtCore.Qt.Key_D: util.key_d,
    QtCore.Qt.Key_E: util.key_e,
    QtCore.Qt.Key_F: util.key_f,
    QtCore.Qt.Key_G: util.key_g,
    QtCore.Qt.Key_H: util.key_h,
    QtCore.Qt.Key_I: util.key_i,
    QtCore.Qt.Key_J: util.key_j,
    QtCore.Qt.Key_K: util.key_k,
    QtCore.Qt.Key_L: util.key_l,
    QtCore.Qt.Key_M: util.key_m,
    QtCore.Qt.Key_N: util.key_n,
    QtCore.Qt.Key_O: util.key_o,
    QtCore.Qt.Key_P: util.key_p,
    QtCore.Qt.Key_Q: util.key_q,
    QtCore.Qt.Key_R: util.key_r,
    QtCore.Qt.Key_S: util.key_s,
    QtCore.Qt.Key_T: util.key_t,
    QtCore.Qt.Key_U: util.key_u,
    QtCore.Qt.Key_V: util.key_v,
    QtCore.Qt.Key_W: util.key_w,
    QtCore.Qt.Key_X: util.key_x,
    QtCore.Qt.Key_Y: util.key_y,
    QtCore.Qt.Key_Z: util.key_z,
    QtCore.Qt.Key_1: util.key_1,
    QtCore.Qt.Key_2: util.key_2,
    QtCore.Qt.Key_3: util.key_3,
    QtCore.Qt.Key_4: util.key_4,
    QtCore.Qt.Key_5: util.key_5,
    QtCore.Qt.Key_6: util.key_6,
    QtCore.Qt.Key_7: util.key_7,
    QtCore.Qt.Key_8: util.key_8,
    QtCore.Qt.Key_9: util.key_9,
    QtCore.Qt.Key_0: util.key_0,
    QtCore.Qt.Key_Space: util.key_space,
    QtCore.Qt.Key_Return: util.key_return,
    QtCore.Qt.Key_Escape: util.key_escape,
}

qtapp = None


def get_qtapp():
    """Gets a `QApplication` instance running.

    Returns the current QApplication instance if it exists and creates it
    otherwise.
    """
    global qtapp
    inst = QtWidgets.QApplication.instance()
    if inst is None:
        qtapp = QtWidgets.QApplication(sys.argv)
    else:
        qtapp = inst
    return qtapp


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        get_qtapp()
        super().__init__()

        self._central_widget = QtWidgets.QWidget(self)
        self._layout = QtWidgets.QStackedLayout(self._central_widget)
        self.setCentralWidget(self._central_widget)

        # status bar shows current participant
        status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(status_bar)
        self._statusbar_label = QtWidgets.QLabel("status")
        status_bar.addPermanentWidget(self._statusbar_label)

        self.show()

    def run(self):
        get_qtapp().exec_()

    def set_view(self, view):
        if self._layout.indexOf(view) == -1:
            self._layout.addWidget(view)

        self._layout.setCurrentWidget(view)

    def set_status(self, message):
        """Adds a status message to the status bar.

        This is typically used for showing the current subject and session
        information.

        Parameters
        ----------
        message : str
            Message to display in the status bar.
        """
        self._statusbar_label.setText(message)

    def keyPressEvent(self, event):
        try:
            key = key_map[event.key()]
        except KeyError:
            return super().keyPressEvent(event)

        self.key_pressed(key)

    @transmitter(('key', str))
    def key_pressed(self, key):
        return key

    def quit(self):
        get_qtapp().quit()

