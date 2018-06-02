import sys
import pytest
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


@pytest.fixture
def memblock():
    return MemoryBlock()


@pytest.fixture
def relayblock():
    return RelayBlock()


@pytest.fixture
def complicatedblock():
    return ComplicatedBlock()


@pytest.fixture
def chainedtransmitters():
    return ChainedTransmittersBlock()


@pytest.fixture
def eventtransmitter():
    return EventTransmitterBlock()


def test_transmitter_connect(memblock, relayblock):
    """Ensure transmitters support `connect` and disconnect."""
    relayblock.relay.link(memblock.remember)
    relayblock.relay(4)
    assert memblock.last_received == 4

    relayblock.relay(8)
    assert memblock.last_received == 8

    relayblock.relay.unlink(memblock.remember)
    relayblock.relay(9.0)
    assert memblock.last_received == 8


def test_receiver_connect(memblock, relayblock):
    """Ensure receivers support `connect` and `disconnect`."""
    memblock.remember.link(relayblock.relay)
    relayblock.relay(2)
    assert memblock.last_received == 2

    memblock.remember.unlink(relayblock.relay)
    relayblock.relay(9)
    assert memblock.last_received == 2


def test_multidata(complicatedblock):
    """Ensure multiple things can be transmitted at once."""
    # transmitter data format specified as tuples
    complicatedblock.tuple_transmitter.link(complicatedblock.set_coords)
    complicatedblock.tuple_transmitter(4, (2.1, 6.2), 42.1)
    assert complicatedblock.coords == (2.1, 6.2)


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="kwarg transmitter format requires Python 3.6+")
def test_transmitter_formats(complicatedblock):
    """Ensure newer data formats work for Python 3.6+."""
    # transmitter data format specified as multiple kwargs
    complicatedblock.dict_transmitter.link(complicatedblock.set_coords)
    complicatedblock.dict_transmitter(4, (4.2, 2.8), 9.8)
    assert complicatedblock.coords == (4.2, 2.8)

    # transmitter data format specified with mixture of args and kwargs
    complicatedblock.mixed_transmitter.link(complicatedblock.set_coords)
    complicatedblock.mixed_transmitter(1, (7.1, 2.4), 59.1)
    assert complicatedblock.coords == (7.1, 2.4)


def test_transmitter_receiver_functions():
    """Use functions (as opposed to methods) as transmitters and receivers."""
    transmit_func.link(recv_func)
    assert transmit_func() == 'message'
    assert message_with_suffix == 'messagesuffix'


def test_chained_transmitters(chainedtransmitters):
    """Chain transmitters together, call the first, then check the result."""
    chainedtransmitters.start.link(chainedtransmitters.intermediate)
    chainedtransmitters.intermediate.link(chainedtransmitters.finish)
    chainedtransmitters.start("hey")
    assert chainedtransmitters.message == "heytouchedoncetouchedtwice"


def test_empty_transmitter(eventtransmitter):
    eventtransmitter.trigger.link(eventtransmitter.on_event)
    assert not hasattr(eventtransmitter, 'event_occurred')
    eventtransmitter.trigger()
    assert hasattr(eventtransmitter, 'event_occurred')
