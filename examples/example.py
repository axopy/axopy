"""
Simple example experiment implementation. Includes a participant selection
tab, an oscilloscope for viewing data in real time, an experiment for recording
that data, and a viewer for viewing the data from the experiment.
"""

from PyQt5 import QtWidgets, QtGui
from numpy import zeros

from axopy.application import (application, ExperimentTask,
                               DataVisualizationTask)
from axopy.storage import ExperimentDatabase, SimpleTrialStorage
from axopy.daq import EmulatedDaq
from axopy.tasks import Oscilloscope
from axopy.pipeline import Pipeline, FeatureExtractor, Windower, Ensure2D
from axopy.features import RMS, MAV


class ExampleExperiment(ExperimentTask):
    """Simple experiment that records raw data."""

    updates_per_trial = 10

    def __init__(self):
        super(ExampleExperiment, self).__init__()
        self._setup_ui()

        self._daq = None
        self.trial = 0

    def setup_daq(self):
        self._daq = self.base_ui.daq_thread

    def shutdown_daq(self):
        if self._daq is None:
            return
        try:
            self._daq.updated.disconnect(self._on_daq_update)
        except TypeError:
            # already disconnected, no big deal
            pass
        if self._daq.running:
            self._daq.kill()

    def setup_storage(self):
        task = self.base_ui.database.require_task(
            self.base_ui.participant, self.__class__.__name__)
        self.db = SimpleTrialStorage(task)
        self.db.create_session('0')

    def _setup_ui(self):
        layout = QtGui.QVBoxLayout()

        self._status_label = QtWidgets.QLabel('')
        layout.addWidget(self._status_label)

        self._list_widget = QtWidgets.QListWidget()
        layout.addWidget(self._list_widget)

        self._button = QtWidgets.QPushButton("Record")
        self._button.clicked.connect(self._on_button_clicked)
        layout.addWidget(self._button)

        self.setLayout(layout)

    def _on_button_clicked(self):
        self._counter = 0
        self._button.setEnabled(False)

        self._daq.updated.connect(self._on_daq_update)
        self._daq.start()

    def _on_daq_update(self, data):
        n_ch, n_samp = data.shape

        # initialize buffer
        if self._counter == 0:
            self._buffer = zeros((n_ch, self.updates_per_trial*n_samp))

        # add data to buffer
        self._buffer[:, self._counter*n_samp:(self._counter+1)*n_samp] = data

        # check for end-of-trial
        if self._counter == self.updates_per_trial - 1:
            self._daq.updated.disconnect(self._on_daq_update)
            self._daq.kill()
            self._button.setEnabled(True)
            self._finish_trial()
        else:
            self._counter += 1

    def _finish_trial(self):
        self._list_widget.addItem('trial')

        # write buffer to storage
        self.db.create_trial(str(self.trial), data=self._buffer)
        self.trial += 1


class ExampleViewer(DataVisualizationTask):
    """Simple viewer for viewing ExampleExperiment data."""

    data_dependencies = ['ExampleExperiment']

    def __init__(self):
        super(ExampleViewer, self).__init__()


if __name__ == '__main__':
    daq = EmulatedDaq(rate=1000, num_channels=2, read_size=100)

    # for this example use memory-backed store instead of file
    db = ExperimentDatabase('file.hdf5', driver='core', backing_store=False)
    db.create_participant('p0')

    pipeline = Pipeline([
        FeatureExtractor([('rms', RMS()), ('mav', MAV())]),
        Ensure2D(),
        Windower(100)])

    with application(daq, db) as app:
        app.install_task(Oscilloscope(pipeline=pipeline))
        app.install_task(ExampleExperiment())
        app.install_task(ExampleViewer())
