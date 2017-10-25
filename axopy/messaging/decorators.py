import functools
from axopy.messaging.qt import transmitter as transmitter_backend


class transmitter(object):
    """Transmitter of events.

    Transmitters are the source of events, and they can send arbitrary data.
    """
    def __init__(self, *args, **kwargs):
        self.data_format = list(args)
        self.data_format.extend(kwargs.items())

    def __call__(self, function):
        return transmitter_backend(function, self.data_format)


class receiver(object):
    """Receivers of events.

    Notes
    -----
    Any Python callbable is a valid receiver, even without the decorator. This
    decorator can be useful for explicitly declaring that a function or method
    is intended to be used as a receiver (i.e. connected to a transmitter
    rather than called directly), and it can be used if you want to connect a
    receiver *to a transmitter* rather than the other way around.
    """
    def __init__(self, function):
        self.function = function
        functools.update_wrapper(self, function)

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
