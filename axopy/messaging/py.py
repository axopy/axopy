from axopy.messaging.base import BaseEmitter


class PyEmitter(BaseEmitter):

    def __init__(self, function, data_format):
        super(PyEmitter, self).__init__(function, data_format)
        self._receiver_funcs = []

    def connect(self, receiver):
        self._receiver_funcs.append(receiver)

    def disconnect(self, receiver):
        self._receiver_funcs.pop(self._receiver_funcs.index(receiver))

    def emit(self, *data):
        print("emitting")
        for c in self._receiver_funcs:
            c(*data)


def emitter(function, data_format):
    return PyEmitter(function, data_format)
