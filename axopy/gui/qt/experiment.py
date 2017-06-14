import sys
from PyQt5 import QtCore, QtWidgets


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


class ExperimentGUI(QtWidgets.QMainWindow):
    """The Qt-backed implementation of an experiment.

    Provides a QMainWindow with a tab widget, where each task gets its own tab
    in the interface.
    """

    def __init__(self):
        get_qtapp()
        super(ExperimentBackend, self).__init__()

        self._setup_ui()
        self.tasks = {}

        self.show()

    def add_task(self, task_ui, name=None):
        """Add a task to the UI.

        Parameters
        ----------
        task_ui: QWidget
            Any widget representing a tasks interface.
        name : str, optional
            Name of the task. Used as the tab label. By default, the class name
            of `task_ui` is used.
        """
        if name is None:
            name = task_ui.__class__.__name__

        self.tasks[name] = task_ui
        self._tab_widget.addTab(task_ui, name)

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

    def run(self):
        get_qtapp().exec_()

    def _setup_ui(self):
        """Initialize widgets and callbacks."""
        # layout
        central_widget = QtWidgets.QWidget(self)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # tab widget -- each tab holds a task
        self._tab_widget = QtWidgets.QTabWidget(central_widget)
        main_layout.addWidget(self._tab_widget)

        # button box for controlling tasks
        self._buttons = _ButtonControls()
        self._buttons.start_clicked.connect(self._on_start_clicked)
        self._buttons.stop_clicked.connect(self._on_stop_clicked)
        main_layout.addWidget(self._buttons)
        self._buttons.setEnabled(False)

        # status bar shows current participant
        status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(status_bar)
        self._statusbar_label = QtWidgets.QLabel("status")
        status_bar.addPermanentWidget(self._statusbar_label)

    def _on_start_clicked(self):
        print("start")

    def _on_stop_clicked(self):
        print("stop")


class _ButtonControls(QtWidgets.QWidget):
    """Start and stop buttons in a horizontal layout used by the main UI."""

    start_clicked = QtCore.pyqtSignal()
    stop_clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(_ButtonControls, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout(self)

        start_button = QtWidgets.QPushButton("Start")
        start_button.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        start_button.clicked.connect(self.start_clicked)
        layout.addWidget(start_button)

        stop_button = QtWidgets.QPushButton("Stop")
        stop_button.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        stop_button.clicked.connect(self.stop_clicked)
        layout.addWidget(stop_button)


