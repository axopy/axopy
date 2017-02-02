import sys
from contextlib import contextmanager
from PyQt5 import QtCore, QtWidgets, QtGui


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


class QtExperimentBackend(QtWidgets.QMainWindow):
    """The Qt-backed implementation of an experiment.

    Provides a QMainWindow with a tab widget, where each task gets its own tab
    in the interface.
    """

    def __init__(self):
        super(QtExperimentBackend, self).__init__()

        self._setup_ui()
        self.tasks = {}

        self.show()

    def add_task(self, task_ui, name):
        """Add a task to the UI.

        Parameters
        ----------
        task_ui: QWidget
            Any widget representing a tasks interface.
        name : str
            Name of the task. Used as the tab label.
        """
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


class ParticipantSelector(QtWidgets.QWidget):
    """A composite QWidget for creating and selecting participants.

    The layout consists of a QListWidget with each item representing a
    participant (text is the participant ID) and a button to create a new
    participant with a modal dialog.

    Attributes
    ----------
    selected : pyqtSignal
        Signal emitted when a participant is selected from the list.
    """

    selected = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(ParticipantSelector, self).__init__(parent=parent)
        self._setup_ui()

    def add_participant(self, pid):
        """Add a participant to the list."""
        self.list_widget.addItem(pid)

    def _setup_ui(self):
        self.main_layout = QtWidgets.QGridLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.main_layout.addWidget(self.label, 0, 0, 1, 1)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemSelectionChanged.connect(
            self._on_participant_selected)
        self.main_layout.addWidget(self.list_widget, 1, 0, 1, 1)

        self.new_button = QtWidgets.QPushButton("New Participant")
        self.new_button.clicked.connect(self._on_new_participant)
        self.main_layout.addWidget(self.new_button, 2, 0, 1, 1)

        self._buttons = _ButtonControls()
        self._buttons.start_clicked.connect(self._on_start_clicked)
        self._buttons.stop_clicked.connect(self._on_stop_clicked)
        main_layout.addWidget(self._buttons)
        self._buttons.setEnabled(False)

    def _on_new_participant(self):
        dialog = NewParticipantDialog(extra_attrs=[('hand', 'Handedness')])
        if not dialog.exec_():
            return

        data = dialog.get_data()
        pid = data['pid']

        # make sure a participant ID was entered
        if pid == '':
            QtWidgets.QMessageBox().warning(
                self,
                "Warning",
                "Participant ID must not be empty.",
                QtWidgets.QMessageBox.Ok)
            return

        # make sure the participant ID doesn't already exist
        found = self.list_widget.findItems(pid, QtCore.Qt.MatchExactly)
        if found:
            # participant ID already in database, select and show warning
            match = found[0]
            self.list_widget.setCurrentItem(match)
            QtWidgets.QMessageBox().warning(
                self,
                "Warning",
                "Participant '{}' already exists in data file.".format(pid),
                QtWidgets.QMessageBox.Ok)
            return

        self.add_participant(pid)

    def _on_participant_selected(self):
        item = self.list_widget.currentItem()
        pid = item.text()
        self.selected.emit(pid)


class NewParticipantDialog(QtWidgets.QDialog):
    """A very simple QDialog for getting a participant ID from the researcher.

    By default, the dialog just shows a QLabel with the text "Participant ID"
    and a QLineEdit next to it to retrieve the ID from the researcher. Ok and
    Cancel buttons are below to accept or cancel the input. Additional
    attributes can be added via the ``extra_attrs`` argument.

    In normal usage, the dialog is shown, the researcher enters the information
    and accepts it by clicking the Ok button, then the data can be retrieved
    with the ``get_data`` method.

    Parameters
    ----------
    extra_attrs : list, optional
        Additional participant attributes for the researcher to fill in. Each
        attribute should be a tuple ``('id', 'label')``, where the id is used
        as a key in the returned data and the label is the text shown next to
        the attribute's input box in the dialog.
    parent : QWidget, optional
        Parent widget of the dialog.
    """

    def __init__(self, extra_attrs=None, parent=None):
        super(NewParticipantDialog, self).__init__(parent=parent)

        if extra_attrs is None:
            extra_attrs = []
        self.extra_attrs = extra_attrs

        self._init_ui()

    def _init_ui(self):
        self.form_layout = QtWidgets.QFormLayout()
        self.line_edits = {}

        attrs = list(self.extra_attrs)
        attrs.insert(0, ('pid', 'Participant ID'))
        for attr, label in attrs:
            edit = QtWidgets.QLineEdit()
            self.line_edits[attr] = edit
            self.form_layout.addRow(label, edit)

        button_box = QtWidgets.QDialogButtonBox()
        button_box.setOrientation(QtCore.Qt.Horizontal)
        button_box.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel |
            QtWidgets.QDialogButtonBox.Ok)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_data(self):
        """Retrieves the data entered in the dialog's fields.

        Returns
        -------
        data : dict
            Dictionary of attributes with the attribute ``id``s as keys and the
            entered text as values.
        """
        return {a: str(e.text()) for a, e in self.line_edits.items()}


if __name__ == '__main__':
    app = get_qtapp()
    exp = QtExperimentBackend()
    app.exec_()
