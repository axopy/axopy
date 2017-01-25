from contextlib import contextmanager
from PyQt5 import QtCore, QtWidgets, QtGui
import copper

from axopy import daq


@contextmanager
def application(*args, **kwargs):
    """Convenience context manager for running an AxoPy application.

    The application instance is created on entry and executed on exit. The
    arguments and keyword arguments are passed along to :class:`BaseUI`, and
    the :class:`BaseUI` instance is yielded.

    Examples
    --------
    This is a sort of pseudo-code example showing how to use the application
    context manager. A couple custom tasks are installed, and the application
    runs upon exit from the context.

    >>> from axopy.application import application
    >>> with application(daq, db) as app:
    ...     app.install_task(CustomTask())
    ...     app.install_task(AnotherCustomTask())
    """
    app = QtWidgets.QApplication([])
    ui = BaseUI(*args, **kwargs)
    yield ui
    ui.show()
    app.exec_()


class Task(QtWidgets.QWidget):
    """Base implementation of a task.

    A task is the core unit of operation in an experiment workflow. Each task
    is presented as a tab in the :class:`BaseUI`.
    """

    requires_participant = False

    def setup_ui(self, parent):
        """Initializes the ``QWidget`` for the task and returns it.

        Parameters
        ----------
        parent : QWidget
            Parent widget of the task.

        Returns
        -------
        widget : QWidget
            The task user interface widget.
        """
        pass

    def setup_daq(self, daq):
        """Initialize the data acquisition thread.

        This method is automatically called when the task is shown. Subclasses
        requiring use of a data acquisition device should override this method
        and perform the following:

            1. set up the thread's processing pipeline
            2. connect the thread's callbacks to methods for handling data
            3. start the thread
        """
        pass

    def setup_storage(self, task_storage, dependencies=None):
        """Initialize data storage for the task.

        This method is automatically called when the task is shown. Subclasses
        requiring use of data storage should override this method.

        Parameters
        ----------
        task_storage : TaskStorage
            Storage belonging to the task.
        dependencies : dict, optional
            Dictionary of :class:`Storage` objects the task depends on,
            accessed by installed name.
        """
        pass

    def shutdown_daq(self):
        """Shut down the data acquisition thread.

        This method is automatically called when the task is hidden.
        Subclasses requiring use of a data acquisition device should override
        this method and perform the following:

            1. disconnect callbacks connected in `setup_daq`
            2. kill the thread
        """
        pass

    def showEvent(self, event):
        """Callback for when the task becomes visible.

        Tasks that become visible check if their requirements are met, and if
        not, disable themselves.
        """
        if self.requires_participant:
            if self.base_ui.participant is None:
                self._participant_requirement_warning()
                self.setEnabled(False)
                return

        self.setEnabled(True)
        self.setup_daq()
        self.setup_storage()

    def hideEvent(self, event):
        self.shutdown_daq()

    def _participant_requirement_warning(self):
        """Shows a warning QMessageBox when a participant is required."""
        QtWidgets.QMessageBox().warning(
            self,
            "Warning",
            "{} requires a participant to be selected.".format(str(self)),
            QtWidgets.QMessageBox.Ok)

    def _daq_requirement_warning(self):
        """Shows a warning QMessageBox when a DAQ is required."""
        QtWidgets.QMessageBox().warning(
            self,
            "Warning",
            "{} requires a data acquisition device to be present.".format(
                str(self)),
            QtWidgets.QMessageBox.Ok)

    def __str__(self):
        return self.__class__.__name__


class BaseUI(QtWidgets.QMainWindow):
    """The base user interface for running experiments.

    Parameters
    ----------
    daq : Daq
        Data acquisition device.
    participant_dialog : class, optional
        A class derived from NewParticipantDialog. By default, a simple dialog
        is shown which contains a single entry for the participant ID.

    Attributes
    ----------
    daq_thread : DaqThread
        Thread running the data acquisition device.
    participant : str
        Currently selected participant.
    """

    def __init__(self, daq, database, parent=None):
        super(BaseUI, self).__init__(parent)
        self._setup_ui()

        self.daq = daq
        self.database = database

        # populate participant list from database
        #for p in self.database.get_participants():
        #    self._particpiant_selector.add_participant(p)

        self.tasks = {}
        self.participant = None
        #self.daq_thread = DaqThread(daq)

    def install_task(self, task, name=None):
        """Add a task to the UI.

        Parameters
        ----------
        task: Task
            Any task extending the base TaskUI class.
        name : str, optional
            Name of the task. Used as the tab label and in the data storage
            hierarchy. By default, the Task's ``str`` is used.
        """
        if name is None:
            name = str(task)

        widget = task.setup_ui()
        self.tasks[name] = task
        self._tab_widget.addTab(widget, name)

    def _setup_ui(self):
        """Initialize widgets and callbacks."""
        # layout
        central_widget = QtWidgets.QWidget(self)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # tab widget -- each tab holds a task
        self._tab_widget = QtWidgets.QTabWidget(central_widget)
        self._tab_widget.setMovable(True)
        main_layout.addWidget(self._tab_widget)

        # participant selection task
        self._particpiant_selector = ParticipantSelector()
        self._particpiant_selector.selected.connect(
            self._on_participant_selected)
        self._tab_widget.addTab(self._particpiant_selector, "Participant")

        # button box for controlling tasks
        self._buttons = _ButtonControls()
        self._buttons.start_clicked.connect(self._on_start_clicked)
        self._buttons.stop_clicked.connect(self._on_stop_clicked)
        main_layout.addWidget(self._buttons)
        self._buttons.setEnabled(False)

        # status bar shows current participant
        status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(status_bar)
        self._statusbar_label = QtWidgets.QLabel("no participant selected")
        status_bar.addPermanentWidget(self._statusbar_label)

    def _on_participant_selected(self, pid):
        """Callback called when a participant is selected."""
        self._statusbar_label.setText("participant: {}".format(pid))
        self.participant = pid

        # enable tabs in the tabwidget for tasks requiring a participant

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


class DaqThread(QtCore.QThread):
    """A QThread for polling data from a data acquisition device.

    Attributes
    ----------
    updated : pyqtSignal
        Emits the latest data from the data acquisition unit as processed by
        the pipeline.
    disconnected : pyqtSignal
        Emitted when there is a problem with the data acquisition unit.
    """

    updated = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal()

    def __init__(self, daq, pipeline=None, parent=None):
        super(DaqThread, self).__init__(parent=parent)
        self.daq = daq

        self._running = False

        if pipeline is None:
            self.pipeline = self._default_pipeline()
        else:
            self.pipeline = pipeline

    @property
    def pipeline(self):
        return self._pipeline

    @pipeline.setter
    def pipeline(self, pipeline):
        was_running = False
        if self._running:
            was_running = True
            self.kill()

        self._pipeline = pipeline

        if was_running:
            self.start()

    def remove_pipeline(self):
        self.pipeline = self._default_pipeline()

    @property
    def running(self):
        return self._running

    def run(self):
        self._running = True

        if self._pipeline is not None:
            self._pipeline.clear()

        self.daq.start()

        while True:
            if not self._running:
                break

            try:
                d = self.daq.read()
            except daq.DisconnectException:
                self.disconnected.emit()
                return

            if self._pipeline is not None:
                self.updated.emit(self._pipeline.process(d))
            else:
                self.updated.emit(d)

        self.daq.stop()

    def kill(self):
        self._running = False
        self.wait()

    def _default_pipeline(self):
        return copper.Pipeline(copper.PipelineBlock())
