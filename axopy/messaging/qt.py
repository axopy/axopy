from axopy.messaging.base import BaseTransmitter
from PyQt5.QtCore import QObject, pyqtSignal


class _QtTransmitter(BaseTransmitter, QObject):

    def connect(self, receiver):
        self.signal.connect(receiver)

    def disconnect(self, receiver):
        try:
            self.signal.disconnect(receiver)
        except TypeError:
            # signal not connected, that's ok
            pass

    def transmit(self, *data):
        self.signal.emit(*data)


def transmitter(function, data_format):
    if data_format:
        _, types = zip(*data_format)
    else:
        types = []
    cls = type('QtTransmitter', (_QtTransmitter,),
               dict(signal=pyqtSignal(*types)))
    return cls(function, data_format)
