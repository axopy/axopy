from contextlib import contextmanager
from PyQt5 import QtCore, QtWidgets, QtGui

from . import daq
from . import pipeline
from .templates.baseui import Ui_BaseUI


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
        """
        Convenience function for creating plugins with default QGridLayout.
        """
        layout = QtWidgets.QGridLayout()
        layout.addWidget(widget)
        self.setLayout(layout)

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

        if self.requires_daq:
            if getattr(self, 'daq', None) is None:
                self._daq_requirement_warning()
                self.setDisabled(True)
                return

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
    record_thread : RecordThread
        Thread running the data acquisition device.
    """

    def __init__(self, daq, database, participant_dialog=None, parent=None):
        super(BaseUI, self).__init__(parent)

        self.daq = daq
        self.database = database

        if participant_dialog is None:
            self.participant_dialog = NewParticipantDialog
        else:
            self.participant_dialog = participant_dialog

        self.tasks = {}

        self.record_thread = RecordThread(daq)

        # initialize form class from Qt Designer-generated UI
        self.ui = Ui_BaseUI()
        self.ui.setupUi(self)

        # set up Ctrl+PgUp and Ctrl+PgDown shortcuts for changing tabs
        nt = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+PgDown"), self)
        nt.activated.connect(self._on_next_tab)
        pt = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+PgUp"), self)
        pt.activated.connect(self._on_prev_tab)

        # populate participant list from database
        for p in self.database.get_participants():
            self.ui.listWidget.addItem(p)
        self.ui.listWidget.itemSelectionChanged.connect(
            self._on_participant_selected)

        self.statusbar_label = QtWidgets.QLabel("no participant selected")
        self.ui.statusbar.addPermanentWidget(self.statusbar_label)

        self.ui.newParticipantButton.clicked.connect(self._on_new_participant)

    @property
    def participant_dialog(self):
        return self._participant_dialog

    @participant_dialog.setter
    def participant_dialog(self, dialog):
        self._participant_dialog = dialog

    def install_task(self, task):
        """
        Add a task to the UI.

        Parameters
        ----------
        task: TaskUI
            Any task extending the base TaskUI class.
        """
        name = str(task)
        #task.set_recorder(self.record_thread)
        self.tasks[name] = task
        self.ui.tabWidget.addTab(task, name)

    def _on_new_participant(self):
        dialog = self.participant_dialog(self)
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
        found = self.ui.listWidget.findItems(pid, QtCore.Qt.MatchExactly)
        if found:
            # participant ID already in database, select and show warning
            match = found[0]
            self.ui.listWidget.setCurrentItem(match)
            QtWidgets.QMessageBox().warning(
                self,
                "Warning",
                "Participant '{}' already exists in data file.".format(pid),
                QtWidgets.QMessageBox.Ok)
            return

        self.ui.listWidget.addItem(pid)

    def _on_participant_selected(self):
        item = self.ui.listWidget.currentItem()
        pid = item.text()
        self.statusbar_label.setText("participant: {}".format(pid))

        for name, task in self.tasks.items():
            if task.requires_participant:
                task.participant = pid

    def _on_next_tab(self):
        i = self.ui.tabWidget.currentIndex() + 1
        if i == self.ui.tabWidget.count():
            i = 0
        self.ui.tabWidget.setCurrentIndex(i)

    def _on_prev_tab(self):
        i = self.ui.tabWidget.currentIndex() - 1
        if i == -1:
            i = self.ui.tabWidget.count() - 1
        self.ui.tabWidget.setCurrentIndex(i)


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


class RecordThread(QtCore.QThread):
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
        super(RecordThread, self).__init__(parent=parent)
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
