from axopy.messaging import transmitter, receiver

class MemoryBlock(object):
    """Just remembers the last thing received."""

    def __init__(self):
        self.last_received = None

    @receiver
    def remember(self, data):
        self.last_received = data


class RelayBlock(object):
    """Just transmits the data its transmitter is called with."""

    @transmitter(number=int)
    def relay(self, number):
        return number


class ComplicatedBlock(object):
    """Block with more complicated transmitter signatures."""

    def __init__(self):
        self.coords = None

    @transmitter(index=int, coords=tuple, height=float)
    def dict_transmitter(self, i, c, h):
        return i, c, h

    @transmitter(('index', int), ('coords', tuple), ('height', float))
    def tuple_transmitter(self, i, c, h):
        return i, c, h

    @transmitter(('index', int), coords=tuple, height=float)
    def mixed_transmitter(self, i, c, h):
        return i, c, h

    @receiver
    def set_coords(self, i, c, h):
        self.coords = c


class ChainedTransmittersBlock(object):
    """Block with stacked transmitter and receiver decorators."""

    @transmitter(msg=str)
    def start(self, msg):
        return msg + "touchedonce"

    @transmitter(msg=str)
    @receiver
    def intermediate(self, msg):
        return msg + "touchedtwice"

    @receiver
    def finish(self, msg):
        self.message = msg


class EventTransmitterBlock(object):
    """Block with a blank transmitter."""

    @transmitter()
    def trigger(self):
        return

    @receiver
    def on_event(self):
        self.event_occurred = True


message_with_suffix = None

@transmitter(msg=str)
def transmit_func():
    return 'message'

@receiver
def recv_func(msg):
    global message_with_suffix
    message_with_suffix = msg + 'suffix'
