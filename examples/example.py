from PyQt5 import QtWidgets, QtGui

from hcibench.application import application, TaskUI
from hcibench.storage import ExperimentDatabase
from hcibench.daq import Daq
from hcibench.tasks import Oscilloscope


class SomeTask(TaskUI):

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


if __name__ == '__main__':
    daq = Daq(2000, 1, (0, 1), 500)

    # for this example use memory-backed store instead of file
    db = ExperimentDatabase('file.hdf5', driver='core', backing_store=False)
    db.create_participant('p0')
    db.create_participant('p1')

    with application(daq, db) as app:
        app.install_task(Oscilloscope())
        app.install_task(SomeTask())
