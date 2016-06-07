from PyQt5 import QtWidgets

from hcibench.base import BaseUI, Plugin
from hcibench.plugins import Oscilloscope
from hcibench.daq import Daq


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    daq = Daq(2000, 1, (0, 1), 500)

    base = BaseUI(daq)
    base.install_utility(Oscilloscope(), show=True)
    base.install_utility(Plugin())

    base.show()
    app.exec_()
