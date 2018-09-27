import sys
from PyQt5 import QtCore, QtWidgets
from axopy import util
from axopy.messaging import Transmitter
import collections
from contextlib import contextmanager

# This mapping from key names in the Qt namespace to axopy key names just
# allows users to write code without any Qt stuff in it
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

qt_key_map = {v: k for k, v in key_map.items()}


def get_qtapp():
    """Get a QApplication instance running.

    Returns the current ``QApplication`` instance if it exists and creates it
    otherwise.

    Examples
    --------
    This function is primarily for internal usage, but it is exposed to make it
    convenient to test graphical code without all of the experiment/task
    machinery.

    .. code-block:: python

        from axopy.gui.main import get_qtapp, Container

        # get the application instance first, before creating widgets etc.
        app = get_qtapp()

        con = Container()

        # call show() to show the widget, then run the application
        con.show()
        app.exec_()
    """
    global qtapp
    inst = QtWidgets.QApplication.instance()
    if inst is None:
        qtapp = QtWidgets.QApplication(sys.argv)
    else:
        qtapp = inst
    return qtapp


@contextmanager
def gui_check():
    """Check graphical interface code interactively.

    This function makes it convenient to test graphical code without all of the
    experiment/task machinery. You can create a :class:`Container`, add things
    to the container, and then call this function with the container to run the
    GUI and try it out.

    .. note::

        Be sure to call :mod:`Container.show()` at the end to display the
        container.

    Examples
    --------
    Minimal example

    .. code-block:: python

        from axopy.gui.main import Container, gui_check

        with gui_check():
            con = Container()
            con.show()
    """
    app = get_qtapp()
    yield app
    app.exec_()


class _MainWindow(QtWidgets.QMainWindow):
    """The window containing all graphical content of the application.

    It is a very simple GUI implemented as a `QMainWindow` with a
    `QStackedLayout` holding a list of :class:`Container` objects. The
    containers, which in turn house all of the interesting graphical content.
    """

    key_pressed = Transmitter(str)

    def __init__(self):
        app = get_qtapp()
        super(_MainWindow, self).__init__()

        app.installEventFilter(self)

        self._central_widget = QtWidgets.QWidget(self)
        self._layout = QtWidgets.QStackedLayout(self._central_widget)
        self.setCentralWidget(self._central_widget)

        status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(status_bar)
        self._statusbar_label = QtWidgets.QLabel("status")
        status_bar.addPermanentWidget(self._statusbar_label)

        self.show()

    def run(self):
        """Start the application."""
        get_qtapp().exec_()

    def new_container(self):
        """Add a new container to the stack and give it back.

        Returns
        -------
        container : Container
            The newly added container.
        """
        c = Container()
        self._layout.addWidget(c)
        self._layout.setCurrentWidget(c)
        return c

    def set_container(self, container):
        """Make the given container visible.

        If the container is already somewhere in the stack, it is just made
        visible, otherwise it is added to the stack.
        """
        if self._layout.indexOf(container) == -1:
            self._layout.addWidget(container)
        self._layout.setCurrentWidget(container)

    def set_status(self, message):
        """Set the status bar message.

        Parameters
        ----------
        message : str
            Message to display in the status bar.
        """
        self._statusbar_label.setText(message)

    def quit(self):
        """Quit the application."""
        get_qtapp().quit()

    def keyPressEvent(self, event):
        """Qt callback for key presses.

        This overrides the `QMainWindow` method. It does not need to be called
        directly and it doesn't need to be overriden. Connect to the
        ``key_pressed`` transmitter to handle key press events.
        """
        try:
            key = key_map[event.key()]
        except KeyError:
            return super().keyPressEvent(event)

        self.key_pressed.emit(key)


class Container(QtWidgets.QWidget):
    """Graphics container for tasks."""

    def set_widget(self, widget):
        """Set the widget containing all graphical elements.

        Parameters
        ----------
        widget : QWidget
            Any QWidget is OK to add.

        See Also
        --------
        axopy.gui.canvas: Canvas widget and canvas items that can be added to
            the container.
        axopy.gui.graph: Plotting widgets that can be added to the container.
        """
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(widget, 0, 0)

    def set_layout(self, layout):
        """Set the layout of the container.

        Parameters
        ----------
        layout : QLayout
            Any QLayout is OK to add.
        """
        self.setLayout(layout)

    def show(self):
        """Show the container in the active application.

        This is not normally needed, unless you're testing out a GUI and using
        :func:`gui_check`.
        """
        super(Container, self).show()


class _SessionConfig(QtWidgets.QDialog):
    """Widget for configuring a session.

    Shows a form layout with the specified options. Options are passed as a
    dictionary with option labels as keys and option types as values. The value
    can also be a sequence of strings, which are shown in a combo box. Use
    ``run()`` to run the dialog and return the results in a dictionary.
    """

    def __init__(self, options):
        app = get_qtapp()
        super(_SessionConfig, self).__init__()
        self.options = options
        self.results = {}
        self.widgets = {}

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setFormAlignment(QtCore.Qt.AlignVCenter)
        main_layout.addLayout(form_layout)

        for label, typ in options.items():
            if typ in {str, int, float}:
                w = QtWidgets.QLineEdit()
                self.widgets[label] = w
                form_layout.addRow(label, w)
            elif isinstance(typ, collections.Sequence):
                w = QtWidgets.QComboBox()
                for choice in typ:
                    w.addItem(str(choice))
                self.widgets[label] = w
                form_layout.addRow(label, w)
            else:
                raise TypeError("option {}({}) not a supported type".format(
                    label, typ))

        button = QtWidgets.QPushButton("Ok")
        main_layout.addWidget(button)
        button.clicked.connect(self._on_button_click)

        self.show()

    def run(self):
        self.exec_()
        return self.results

    def _on_button_click(self):
        for label, widget in self.widgets.items():
            t = self.options[label]
            if t is str:
                self.results[label] = str(widget.text())
            elif t is int:
                self.results[label] = int(widget.text())
            elif t is float:
                self.results[label] = float(widget.text())
            else:
                self.results[label] = str(widget.currentText())

        if 'subject' in self.options and self.results['subject'] == '':
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Subject ID must not be empty.",
                QtWidgets.QMessageBox.Ok)
            return

        self.done(0)
