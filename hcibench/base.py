from PyQt5 import QtCore, QtWidgets, QtGui
from hcibench import daq
from hcibench import pipeline
from hcibench.templates.baseui import Ui_BaseUI


class TaskUI(QtWidgets.QWidget):
    """
    Base task that does nothing.
    """

    def set_recorder(self, recorder):
        self.recorder = recorder

    def set_central_widget(self, widget):
        """
        Convenience function for creating plugins with default QGridLayout.
        """
        layout = QtWidgets.QGridLayout()
        layout.addWidget(widget)
        self.setLayout(layout)

    def setup_recorder(self):
        """
        Register recorder callbacks.
        """
        pass

    def dispose_recorder(self):
        """
        Un-register recorder callbacks.
        """
        pass

    def showEvent(self, event):
        self.setup_recorder()

    def hideEvent(self, event):
        self.dispose_recorder()

    def __str__(self):
        return self.__class__.__name__


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
    """

    def __init__(self, daq, database, participant_dialog=None, parent=None):
        super(BaseUI, self).__init__(parent)

        self.ui = Ui_BaseUI()
        self.ui.setupUi(self)

        # set up Ctrl+PgUp and Ctrl+PgDown shortcuts for changing tabs
        nt = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+PgDown"), self)
        nt.activated.connect(self._on_next_tab)
        pt = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+PgUp"), self)
        pt.activated.connect(self._on_prev_tab)

        self.daq = daq
        self.record_thread = RecordThread(daq)

        self.database = database
        for p in self.database.get_participants():
            self.ui.listWidget.addItem(p)

        if participant_dialog is None:
            self.participant_dialog = NewParticipantDialog
        else:
            self.participant_dialog = participant_dialog

        self.tasks = {}

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
        task.set_recorder(self.record_thread)
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

    def _on_next_tab(self):
        print("hey")
        i = self.ui.tabWidget.currentIndex() + 1
        if i == self.ui.tabWidget.count():
            i = 0
        self.ui.tabWidget.setCurrentIndex(i)

    def _on_prev_tab(self):
        i = self.ui.tabWidget.currentIndex() - 1
        if i == -1:
            i = self.ui.tabWidget.count() - 1
        self.ui.tabWidget.setCurrentIndex(i)

    def showEvent(self, event):
        if not self.record_thread.running:
            self.record_thread.start()

    def closeEvent(self, event):
        if self.record_thread is not None:
            self.record_thread.kill()


class NewParticipantDialog(QtWidgets.QDialog):
    """
    A very simple QDialog for getting a participant ID from the operator.

    This class is intentionally easy to extend so experiments can specify
    additional participant attributes to input. Define a class which inherits
    from this one and specify the class attribute ``attributes``, which should
    be a list of tuples ``('attribute_id', 'Attribute Label')``.  The attribute
    ID is used as the key to retrieving the input once the dialog is accepted,
    and the attribute label is what's shown in the dialog.

    Examples
    --------
    >>> from hcibench.base import NewParticipantDialog
    >>> class CustomDialog(NewParticipantDialog):
    ...     attributes = [('handedness', 'Handedness'),
    ...                   ('gender', 'Gender')]
    """

    attributes = []

    def __init__(self, parent=None):
        super(NewParticipantDialog, self).__init__(parent=parent)

        self._init_ui()

    def _init_ui(self):
        self.form_layout = QtWidgets.QFormLayout()
        self.line_edits = {}

        attrs = list(self.attributes)
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

    Signals
    -------
    updated :
        Emits the latest data from the data acquisition unit as processed by
        the pipeline.
    disconnected :
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
