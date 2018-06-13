import functools
from axopy.messaging.qt import transmitter as transmitter_backend


class transmitter(object):
    """Decorator for functions which transmit events and/or data.

    You can decorate any method or function with ``@transmitter()`` to make it
    a transmitter. The decorator accepts arguments which specify the
    transmitter's "data format." Each argument is a tuple specifying the item
    name and the type.

    Examples
    --------
    Here is an example of an "event transmitter" (i.e. a transmitter which
    doesn't send any data):

    >>> from axopy.messaging import transmitter
    >>> @transmitter()
    ... def event():
    ...     return
    ...
    >>> def event_recv():
    ...     print("event received!")
    ...
    >>> event.connect(event_recv)
    >>> event()
    event received!

    If you want to transmit data, you specify the name and type of each item
    returned. Notice that the receiver needs to take the correct number of
    arguments (but the names of the arguments *don't* need to match the
    transmitter's data format). Also note that when the transmitter function is
    called at the end, its data is returned *and* the receiver receives the
    data.

    >>> @transmitter(('msg', str), ('num', float))
    ... def data_tx():
    ...     return 'hello', 4.2
    ...
    >>> def data_rx(msg, num):
    ...     print("received: %s, %f" % (msg, num))
    ...
    >>> data_tx.connect(data_rx)
    >>> data_tx()
    received: hello, 4.200000
    ('hello', 4.2)


    """
    def __init__(self, *args, **kwargs):
        self.data_format = list(args)
        self.data_format.extend(kwargs.items())

    def __call__(self, function):
        dec = transmitter_backend(function, self.data_format)
        dec.__doc__ = function.__doc__
        dec.__module__ = function.__module__
        dec.__name__ = function.__name__
        return dec


class receiver(object):
    """Receiver of events.

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
