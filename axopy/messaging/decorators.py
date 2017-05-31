import importlib
from axopy import settings

if isinstance(settings.messaging_backend, str):
    mod = importlib.import_module(
        'axopy.messaging.{}'.format(settings.messaging_backend.lower()))
    settings.messaging_backend = mod.transmitter


class transmitter(object):
    def __init__(self, *args, **kwargs):
        self.data_format = list(args)
        self.data_format.extend(kwargs.items())

    def __call__(self, function):
        return settings.messaging_backend(function, self.data_format)


class receiver(object):
    def __init__(self, function):
        self.function = function

    def __get__(self, inst, cls):
        self.inst = inst
        self.cls = cls
        return self

    def __call__(self, *args, **kwargs):
        if hasattr(self, 'inst'):
            result = self.function(self.inst, *args, **kwargs)
        else:
            result = self.function(*args, **kwargs)
        return result

    def connect(self, transmitter):
        transmitter.connect(self)

    def disconnect(self, transmitter):
        transmitter.disconnect(self)
