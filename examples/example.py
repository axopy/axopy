from PyQt5 import QtWidgets, QtGui

from hcibench.base import BaseUI, TaskUI, NewParticipantDialog
from hcibench.storage import ExperimentDatabase
from hcibench.plugins import Oscilloscope
from hcibench.daq import Daq


class CustomParticipantDialog(NewParticipantDialog):
    attributes = [('handedness', 'Handedness'),
                  ('gender', 'Gender')]


class SomeTask(TaskUI):

    def __init__(self, parent=None):
        super(SomeTask, self).__init__(parent=parent)

        self._init_ui()

    def _init_ui(self):
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
    app = QtWidgets.QApplication([])

    daq = Daq(2000, 1, (0, 1), 500)

    # for this example use memory-backed store instead of file
    db = ExperimentDatabase('file.hdf5', driver='core', backing_store=False)
    db.create_participant('p0')
    db.create_participant('p1')

    base = BaseUI(daq, db, participant_dialog=CustomParticipantDialog)
    base.install_task(Oscilloscope())
    base.install_task(SomeTask())

    base.show()
    app.exec_()
