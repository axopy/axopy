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


class ParticipantSelector(QtWidgets.QWidget):
    """A composite QWidget for creating and selecting participants.

    The layout consists of a `QListWidget` with each item representing a
    participant (text is the participant ID) and a button to create a new
    participant with a modal dialog. The modal dialog is populated with
    customizable fields (see `extra_args`).

    When a participant is selected from the list, a dictionary is emitted
    via the `selected` signal. The dictionary always contains a 'pid' item and
    any other items added via the `extra_args` list.

    Parameters
    ----------
    extra_attrs : list, optional
        Additional participant attributes for the researcher to fill in. Each
        attribute should be a tuple `('id', 'label')`, where the id is used as
        a key in the returned data and the label is the text shown next to the
        attribute's input box in the dialog.
    parent : QObject, optional
        Qt parent object.

    Attributes
    ----------
    selected : pyqtSignal
        Signal emitted when a participant is selected from the list.
    """

    selected = QtCore.pyqtSignal(dict)

    def __init__(self, extra_attrs=None, parent=None):
        super(ParticipantSelector, self).__init__(parent=parent)
        self._setup_ui()

        self.participant_attrs = [('pid', "Participant ID")]
        if extra_attrs is not None:
            self.participant_attrs.extend(extra_attrs)

        self.participants = {}

    def add_participant(self, participant):
        """Add a participant to the list.

        Parameters
        ----------
        participant : str or dict
            Participant data. If just a string is used, it is assumed to be the
            participant's ID. If a dictionary is used, it may include
            additional attributes (e.g. handedness, age, etc.), but it must
            include a 'pid' item.
        """
        if isinstance(participant, str):
            participant = {'pid': participant}

        self.participants[participant['pid']] = participant
        self.list_widget.addItem(participant['pid'])

    def _setup_ui(self):
        """User interface setup for __init__ cleanliness."""
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.main_layout.addWidget(self.label)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemSelectionChanged.connect(
            self._on_participant_selected)
        self.main_layout.addWidget(self.list_widget)

        self.new_button = QtWidgets.QPushButton("New Participant")
        self.new_button.clicked.connect(self._on_new_participant)
        self.main_layout.addWidget(self.new_button)

    def _on_new_participant(self):
        """Callback for when the "New Participant" button is pressed.

        Opens up a FormDialog to enter informaiton, then does some checking to
        make sure the entered information makes sense.
        """
        dialog = FormDialog(self.participant_attrs)
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
            # participant ID already in the list, select and show warning
            match = found[0]
            self.list_widget.setCurrentItem(match)
            QtWidgets.QMessageBox().warning(
                self,
                "Warning",
                "Participant '{}' already exists.".format(pid),
                QtWidgets.QMessageBox.Ok)
            return

        self.add_participant(data)

    def _on_participant_selected(self):
        """Callback for when an item in the list is selected."""
        item = self.list_widget.currentItem()
        pid = item.text()
        participant = self.participants[pid]
        self.selected.emit(participant)


class FormDialog(QtWidgets.QDialog):
    """A simple form dialog for entering information.

    The dialog just contains a set of rows with a `QLabel` and a `QLineEdit`
    in each row. Ok and Cancel buttons are below to accept or cancel the input.

    In normal usage, the dialog is shown, the researcher enters the information
    and accepts it by clicking the Ok button, then the data can be retrieved
    with the `get_data` method.

    Parameters
    ----------
    attrs : list
        Form elements for the researcher to fill in. Each attribute should be a
        tuple `('id', 'label')`, where the id is used as a key in the returned
        data and the label is the text shown next to the attribute's input box
        in the dialog.
    parent : QWidget, optional
        Parent widget of the dialog.
    """

    def __init__(self, attrs, parent=None):
        super(FormDialog, self).__init__(parent=parent)
        self.attrs = attrs
        self._init_ui()

    def _init_ui(self):
        """Construct widgets in the form layout."""
        self.form_layout = QtWidgets.QFormLayout()
        self.line_edits = {}

        for attr, label in self.attrs:
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
            Dictionary of attributes with the attribute `id`s as keys and the
            entered text as values.
        """
        return {a: str(e.text()) for a, e in self.line_edits.items()}


class TestExperiment(object):

    def __init__(self):
        get_qtapp()
        self.backend = QtExperimentBackend()

        selector = ParticipantSelector(extra_attrs=[('hand', "Handedness")])
        selector.add_participant('p0')
        selector.add_participant('s4')
        self.backend.add_task(selector, name='Select Participant')

        selector.selected.connect(self.participant_selected)

    def run(self):
        get_qtapp().exec_()

    def participant_selected(self, participant):
        print(participant)


if __name__ == '__main__':
    exp = TestExperiment()
    exp.run()
