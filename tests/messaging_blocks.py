from axopy.messaging import emitter, receiver

class MemoryBlock(object):
    """Just remembers the last thing received."""

    def __init__(self):
        self.last_received = None

    @receiver
    def remember(self, data):
        self.last_received = data


class RelayBlock(object):
    """Just emits the data its emitter is called with."""

    @emitter(number=int)
    def relay(self, number):
        return number


class ComplicatedBlock(object):
    """Block with a more complicated emitter signature."""

    def __init__(self):
        self.coords = None

    @emitter(index=int, coords=tuple, height=float)
    def emitter(self, i, c, h):
        return i, c, h

    @receiver
    def receiver(self, i, c, h):
        self.coords = c


message_with_suffix = None

@emitter(msg=str)
def emit_func():
    return 'message'

@receiver
def recv_func(msg):
    global message_with_suffix
    message_with_suffix = msg + 'suffix'
