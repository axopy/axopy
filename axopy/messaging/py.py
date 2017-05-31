from axopy.messaging.base import BaseTransmitter


class PyTransmitter(BaseTransmitter):

    def __init__(self, function, data_format):
        super(PyTransmitter, self).__init__(function, data_format)
        self._receiver_funcs = []

    def connect(self, receiver):
        self._receiver_funcs.append(receiver)

    def disconnect(self, receiver):
        self._receiver_funcs.pop(self._receiver_funcs.index(receiver))

    def transmit(self, *data):
        for c in self._receiver_funcs:
            c(*data)


def transmitter(function, data_format):
    return PyTransmitter(function, data_format)
