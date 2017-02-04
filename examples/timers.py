import time
from PyQt5 import QtCore, QtWidgets


# represents an input device
class CounterThread(QtCore.QThread):

    updated = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(CounterThread, self).__init__(parent=parent)

        self._running = False

    @property
    def running(self):
        return self._running

    def run(self):
        self._running = True

        while True:
            time.sleep(0.1)

            if not self._running:
                break

            self.updated.emit()

    def kill(self):
        self._running = False
        self.wait()


class IncrementalTimer(QtCore.QObject):

    timeout = QtCore.pyqtSignal()

    def __init__(self, interval=0):
        super(IncrementalTimer, self).__init__()

        self.interval = interval
        self.count = 0

    @QtCore.pyqtSlot()
    def increment(self):
        self.count += 1

        if self.count == self.interval:
            self.timeout.emit()
            self.reset()

    def reset(self):
        self.count = 0


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    win = QtWidgets.QMainWindow()

    timer = IncrementalTimer(5)
    thread = CounterThread()

    thread.updated.connect(timer.increment)
    timer.timeout.connect(thread.kill)

    thread.start()

    win.show()
    app.exec_()
