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
    """Block with more complicated emitter signatures."""

    def __init__(self):
        self.coords = None

    @emitter(index=int, coords=tuple, height=float)
    def dict_emitter(self, i, c, h):
        return i, c, h

    @emitter(('index', int), ('coords', tuple), ('height', float))
    def tuple_emitter(self, i, c, h):
        return i, c, h

    @emitter(('index', int), coords=tuple, height=float)
    def mixed_emitter(self, i, c, h):
        return i, c, h

    @receiver
    def set_coords(self, i, c, h):
        self.coords = c


class ChainedEmittersBlock(object):
    """Block with stacked emitter and receiver decorators."""

    @emitter(msg=str)
    def start(self, msg):
        return msg + "touchedonce"

    @emitter(msg=str)
    @receiver
    def intermediate(self, msg):
        return msg + "touchedtwice"

    @receiver
    def finish(self, msg):
        self.message = msg


class EventEmitterBlock(object):
    """Block with a blank emitter."""

    @emitter()
    def trigger(self):
        return

    @receiver
    def on_event(self):
        self.event_occurred = True


message_with_suffix = None

@emitter(msg=str)
def emit_func():
    return 'message'

@receiver
def recv_func(msg):
    global message_with_suffix
    message_with_suffix = msg + 'suffix'
