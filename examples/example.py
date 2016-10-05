from PyQt5 import QtWidgets, QtGui

from axopy.application import application, ExperimentTask
from axopy.storage import ExperimentDatabase
from axopy.daq import EmulatedDaq
from axopy.tasks import Oscilloscope
from axopy.pipeline import Pipeline, PipelineBlock, FeatureExtractor, Windower
from axopy.features import RMS
from axopy.util import ensure_2d


class SomeTask(ExperimentTask):

    def __init__(self):
        super(SomeTask, self).__init__()

        layout = QtGui.QVBoxLayout()

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)

        self.button = QtWidgets.QPushButton("Click!")
        self.button.clicked.connect(self._on_button_clicked)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def _on_button_clicked(self):
        self.list_widget.addItem("button clicked")


class Ensure2D(PipelineBlock):
    def process(self, data):
        data = ensure_2d(data)
        return data.T


def build_pipeline():
    pipeline = Pipeline([
        FeatureExtractor([('rms', RMS())]),
        Ensure2D(),
        Windower(100)])
    return pipeline


if __name__ == '__main__':
    daq = EmulatedDaq(rate=1000, num_channels=2, read_size=100)

    # for this example use memory-backed store instead of file
    db = ExperimentDatabase('file.hdf5', driver='core', backing_store=False)
    db.create_participant('p0')
    db.create_participant('p1')

    with application(daq, db) as app:
        app.install_task(Oscilloscope(pipeline=build_pipeline()))
        app.install_task(SomeTask())
        app.install_task(ExperimentTask())
