from contextlib import contextmanager
from PyQt5 import QtCore, QtWidgets, QtGui

from axopy import daq
from axopy import pipeline


@contextmanager
def application(*args, **kwargs):
    """
    Convenience context manager for running a :class:`BaseUI` in a
    QApplication. The application instance is created on entry and executed on
    exit. The arguments and keyword arguments are passed along to
    :class:`BaseUI`, and the :class:`BaseUI` instance is yielded.

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


class TaskUI(QtWidgets.QWidget):
    """Base implementation of a task.

    A task is the core unit of operation in an experiment workflow. Each task
    is presented as a tab in the :class:`BaseUI`.

    Attributes
    ----------
    requires_daq : bool
        True if the task requires a data acquisition device to run.
    requires_participant : bool
        True if the task requires a participant to be selected to run.
    """

    requires_daq = False
    requires_participant = False

    def set_central_widget(self, widget):
        """Convenience method for setting up a single-widget interface.

        The widget is placed in a :class:`QGridLayout`, and the layout is set
        as the tab's layout.

        Parameters
        ----------
        widget : QWidget
            The widget to use as the interface.
        """
        layout = QtWidgets.QGridLayout()
        layout.addWidget(widget)
        self.setLayout(layout)

    def setup_daq(self):
        """Initialize the data acquisition thread.

        This method is automatically called when hte task is shown. Subclasses
        requiring use of a data acquisition device should override this method
        and perform the following:

            1. set up the thread's processing pipeline
            2. connect the thread's callbacks to methods for handling data
            3. start the thread
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
            if getattr(self, 'participant', None) is None:
                self._participant_requirement_warning()
                self.setDisabled(True)
                return

        self.setup_daq()

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


class RealtimeVisualizationTask(TaskUI):
    """Task type meant for displaying data from a data acquisition device.

    These tasks require a data acquisition device, and while they can
    implement a processing pipeline before displaying the data, these tasks
    cannot write the data to storage. See :class:`ExperimentTask` for a task
    type that handles displaying data from a DAQ and writing data to storage.
    """

    requires_daq = True


class DataVisualizationTask(TaskUI):
    """Task type meant for displaying data from storage.

    These tasks require access to data storage from another task in order to
    display it in some way.
    """

    requires_participant = True


class ProcessingTask(TaskUI):
    """Task type meant for generating new data from another task's output.

    These tasks require access to data storage from another task as well as
    the ability to write data to storage.
    """

    requires_participant = True


class ExperimentTask(TaskUI):
    """Task type meant for implementing the full suite of axopy capabilities.

    These tasks are endowed with reading data from a data acquisition device,
    using data output by other tasks, and writing data to storage.
    """

    requires_daq = True
    requires_participant = True


class BaseUI(QtWidgets.QMainWindow):
    """
    The base user interface for running experiments.

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
    """

    def __init__(self, daq, database, parent=None):
        super(BaseUI, self).__init__(parent)
        self._setup_ui()

        self.daq = daq
        self.database = database

        # populate participant list from database
        for p in self.database.get_participants():
            self._particpiant_selector.add_participant(p)

        self.tasks = {}

        self.daq_thread = DaqThread(daq)

    def install_task(self, task):
        """
        Add a task to the UI.

        Parameters
        ----------
        task: TaskUI
            Any task extending the base TaskUI class.
        """
        name = str(task)
        self.tasks[name] = task
        self._tab_widget.addTab(task, name)
        task.base_ui = self

    def _setup_ui(self):
        """Initialize widgets and callbacks."""
        # layout
        central_widget = QtWidgets.QWidget(self)
        main_layout = QtWidgets.QGridLayout(central_widget)
        self.setCentralWidget(central_widget)

        # tab widget -- each tab holds a task
        self._tab_widget = QtWidgets.QTabWidget(self)
        self._tab_widget.setMovable(True)
        main_layout.addWidget(self._tab_widget)

        # participant selection task
        self._particpiant_selector = ParticipantSelector()
        self._particpiant_selector.selected.connect(
            self._on_participant_selected)
        self._tab_widget.addTab(self._particpiant_selector, "Participant")

        # status bar shows current participant
        status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(status_bar)
        self._statusbar_label = QtWidgets.QLabel("no participant selected")
        status_bar.addPermanentWidget(self._statusbar_label)

        # set up Ctrl+PgUp and Ctrl+PgDown shortcuts for changing tabs
        nexttab = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+PgDown"), self)
        nexttab.activated.connect(self._on_ctrl_pgdown)
        prevtab = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+PgUp"), self)
        prevtab.activated.connect(self._on_ctrl_pgup)

    def _on_participant_selected(self, pid):
        """Callback called when a participant is selected."""
        self._statusbar_label.setText("participant: {}".format(pid))

    def _on_ctrl_pgdown(self):
        """Callback for switching to next tab on Ctrl+PagDown."""
        i = self._tab_widget.currentIndex() + 1
        if i == self._tab_widget.count():
            i = 0
        self._tab_widget.setCurrentIndex(i)

    def _on_ctrl_pgup(self):
        """Callback for switching to previous tab on Ctrl+PagDown."""
        i = self._tab_widget.currentIndex() - 1
        if i == -1:
            i = self._tab_widget.count() - 1
        self._tab_widget.setCurrentIndex(i)


class ParticipantSelector(QtWidgets.QWidget):

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
        dialog = NewParticipantDialog()
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
    """
    A very simple QDialog for getting a participant ID from the operator.

    This class is intentionally easy to extend so experiments can specify
    additional participant attributes to input. Define a class which inherits
    from this one and specify the class attribute ``extra_attributes``, which
    should be a list of tuples ``('attribute_id', 'Attribute Label')``.  The
    attribute ID is used as the key to retrieving the input once the dialog is
    accepted, and the attribute label is what's shown in the dialog.

    Examples
    --------
    >>> from axopy.base import NewParticipantDialog
    >>> class CustomDialog(NewParticipantDialog):
    ...     extra_attributes = [('handedness', 'Handedness'),
    ...                         ('gender', 'Gender')]
    """

    extra_attributes = []

    def __init__(self, parent=None):
        super(NewParticipantDialog, self).__init__(parent=parent)

        self._init_ui()

    def _init_ui(self):
        self.form_layout = QtWidgets.QFormLayout()
        self.line_edits = {}

        attrs = list(self.extra_attributes)
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
        return {a: str(e.text()) for a, e in self.line_edits.items()}


class DaqThread(QtCore.QThread):
    """
    Retrieves data from a data acquisition device in a separate thread.

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
        return pipeline.Pipeline(pipeline.PipelineBlock())
