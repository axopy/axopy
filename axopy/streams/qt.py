class InputStreamBackend(QtCore.QThread):
    """QThread backend for an `InputStream`.

    Runs a persistent while loop wherein the InputStream device is repeatedly
    polled for data. When the data becomes available, it is emitted and the
    loop continues.

    Parameters
    ----------
    device : OutputDevice
        Any object implementing the OutputDevice interface. See EmulatedDaq for
        an example.

    Attributes
    ----------
    updated : pyqtSignal
        Emits the latest data from the data acquisition unit as processed by
        the pipeline.
    disconnected : pyqtSignal
        Emitted when there is a problem with the data acquisition unit.
    """

    # TODO: wrap these in messaging abstraction
    updated = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal()

    def __init__(self, device):
        super(DaqThread, self).__init__()
        self.device = device

        self._running = False

    @property
    def running(self):
        return self._running

    def run(self):
        self._running = True

        self.device.start()

        while True:
            if not self._running:
                break

            try:
                d = self.device.read()
            except IOError:
                self.disconnected.emit()
                return

            self.updated.emit(d)

        self.device.stop()

    def kill(self):
        self._running = False
        self.wait()
