from axopy.messaging.base import BaseTransmitter
from PySide2.QtCore import QObject, Signal


class _QtTransmitter(BaseTransmitter, QObject):

    def link(self, receiver):
        self.signal.connect(receiver)

    def unlink(self, receiver):
        try:
            self.signal.disconnect(receiver)
        except (TypeError, RuntimeError):
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
               dict(signal=Signal(*types)))
    obj = cls(function, data_format)
    return obj
