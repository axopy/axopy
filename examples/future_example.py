"""
This is a pseudo-code-ish example for me to figure out how making a custom
experiment should look once the library is more complete.
"""

from PyQt5 import QtCore, QtWidgets, QtGui

from axopy import daq
from axopy import pipeline
from axopy import application


# "data" that is global to the experiment
gesture_mapping = {
    0: 'rest',
    1: 'open-hand',
    2: 'close-hand'
}


# 1. define custom tasks
#   - each custom task should be in a separate module or maybe all custom
#     custom tasks could be put in a single module `tasks.py`
#   - a task is something that the researcher instantiates in the entry point,
#     but the main UI is able to start a new run with it


# here's a class implementing a task
class TACTask(object):

    # the experiment UI uses this attribute to generate a dialog when creating
    # a new run of this task
    params = {
        'hand': ('right', 'left', 'right'),
        'limb': ('arm', 'leg', 'arm'),
    }

    def __init__(self, pipeline, task_storage, train_storage):
        self.pipeline = pipeline
        self.task_storage = task_storage
        self.train_storage = train_storage

    def create(self, subject_id, run_id):
        """Called when the task is shown.

        Need to make sure stateful attributes are cleared and initialized.

        Must return the task UI.
        """
        self._subject_id = subject_id
        self._run_id = run_id

        self._current_trial = 0
        self.task_storage.create_run(subject_id, run_id)

        self.ui = TACTaskUI()
        self.ui.start_clicked.connect(self._on_start)
        self.ui.pause_clicked.connect(self._on_pause)

    def _on_train(self):
        """Callback for `train` button."""
        data = self.train_storage.collect_sessions(self._subject,
                                                   self._selected_sessions)
        self.pipeline.named_blocks('classifier').fit(*data)

    def _on_start(self):
        """Callback for `start` button."""

        # experiment UI can disable other tabs and stuff
        self.locked.emit()

    def _on_pause(self):

        # experiment UI enables other tabs
        self.unlocked.emit()


# it's a good idea to separate the Qt UI code from the task implementation
class TACTaskUI(QtWidgets.QWidget):

    start_clicked = QtCore.pyqtSignal()
    pause_clicked = QtCore.pyqtSignl()

    def __init__(self):
        layout = QtGui.QVBoxLayout()

        self._status_label = QtWidgets.QLabel('')
        layout.addWidget(self._status_label)

        self._list_widget = QtWidgets.QListWidget()
        layout.addWidget(self._list_widget)

        self._start_button = QtWidgets.QPushButton("Record")
        self._start_button.clicked.connect(self._on_start_clicked)
        layout.addWidget(self._start_button)

        self._pause_button = QtWidgets.QPushButton("Pause")
        self._pause_button.clicked.connect(self._on_pause_clicked)
        layout.addWidget(self._pause_button)

        self.setLayout(layout)

    def _on_start_clicked(self):
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


# 2. write functions to set up each task
#   - task implementations should be fairly general (e.g. a specific pipeline
#     isn't enforced), so some things need to be set up to be passed in to
#     the tasks __init__
#   - having a separate function to do the setup allows `main()` to look like
#     a high level overview of the task


def setup_oscilloscope(daq):
    pipeline = Pipeline(
        [
            daq,
            FeatureExtractor([
                ('rms', exg.root_mean_square),
                ('ssc', exg.slope_sign_changes, {'threshold': 0.01})
            ]),
            Ensure2D(),
            Windower(100)
        ]
    )

    return Oscilloscope(pipeline)


def setup_train_task(daq, db):
    def img_path(name):
        return pkg_resources.resource_filename(
            os.path.join(__name__, 'images', name+'.png'))

    pipeline = Pipeline([daq])
    imgs = [l: img_path(n) for l, n in gesture_mapping.items()]

    task_storage = db.require_task('TrainTask')

    return ImageTrainingTask(pipeline, images=imgs, task_storage=task_storage)


def setup_tac_task(daq, db):
    pipeline = Pipeline(
        [
            daq,
            FeatureExtractor([
                ('rms', RMS()),
                ('ssc', SSC()),
                ('wl', WL())
            ]),
            Estimator(LinearDiscriminantAnalysis(), name='classifier'),
            DBVRController({0: 'rest', 1: 'open-hand', 2: 'close-hand'})
        ]
    )

    task_storage = db.require_task('TACTask')
    train_storage = db.require_task('TrainTask')

    return TACTask(pipeline, task_storage, train_storage)


# 3. write an entry point
#   - set up storage and a data source
#   - initialize the main application
#   - set up and install the tasks


def main():
    # objects global to the experiment
    daq = EmulatedDaq(rate=1000, num_channels=2, read_size=100)
    db = ExperimentDatabase('file.hdf5', 'a')

    # create the main UI and install tasks to it
    with application.application(db) as app:
        app.install_task(setup_oscilloscope(daq))
        app.install_task(setup_train_task(daq, db))
        app.install_task(setup_tac_task(daq, db))


if __name__ == '__main__':
    main()
