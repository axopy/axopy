from axopy.messaging.base import BaseEmitter
from PyQt5.QtCore import QObject, pyqtSignal


class _QtEmitterBase(BaseEmitter, QObject):

    def connect(self, receiver):
        self.signal.connect(receiver)

    def disconnect(self, receiver):
        self.signal.disconnect(receiver)

    def emit(self, *data):
        self.signal.emit(*data)


def emitter(function, data_format):
    cls = type('QtEmitter', (_QtEmitterBase,),
               dict(signal=pyqtSignal(*data_format.values())))
    return cls(function, data_format)
