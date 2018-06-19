import sys
import pytest
from axopy.messaging import Transmitter, TransmitterBase


class MemoryBlock(object):
    """Just remembers the last thing received."""

    def __init__(self):
        self.last_received = None

    def remember(self, data):
        self.last_received = data


class RelayBlock(TransmitterBase):
    """Just transmits the data its transmitter is called with."""
    relay = Transmitter(int)


class ComplicatedBlock(TransmitterBase):
    """Block with more complicated transmitter signatures."""
    tx = Transmitter(int, tuple, float)

    def __init__(self):
        super(ComplicatedBlock, self).__init__()
        self.coords = None

    def set_coords(self, i, c, h):
        self.coords = c


class ChainedTransmittersBlock(TransmitterBase):
    """Block with stacked transmitter and receiver decorators."""

    start = Transmitter(str)
    intermediate = Transmitter(str)

    def finish(self, msg):
        self.message = msg


class EventTransmitterBlock(TransmitterBase):
    """Block with a blank transmitter."""
    trigger = Transmitter()

    def on_event(self):
        self.event_occurred = True


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
    relayblock.relay.connect(memblock.remember)
    relayblock.relay.emit(4)
    assert memblock.last_received == 4

    relayblock.relay.emit(8)
    assert memblock.last_received == 8

    relayblock.relay.disconnect(memblock.remember)
    relayblock.relay.emit(9.0)
    assert memblock.last_received == 8


def test_multidata(complicatedblock):
    """Ensure multiple things can be transmitted at once."""
    # transmitter data format specified as tuples
    complicatedblock.tx.connect(complicatedblock.set_coords)
    complicatedblock.tx.emit(4, (2.1, 6.2), 42.1)
    assert complicatedblock.coords == (2.1, 6.2)


def test_chained_transmitters(chainedtransmitters):
    """Chain transmitters together, call the first, then check the result."""
    chainedtransmitters.start.connect(chainedtransmitters.intermediate)
    chainedtransmitters.intermediate.connect(chainedtransmitters.finish)
    chainedtransmitters.start.emit("hey")
    assert chainedtransmitters.message == "hey"


def test_empty_transmitter(eventtransmitter):
    eventtransmitter.trigger.connect(eventtransmitter.on_event)
    assert not hasattr(eventtransmitter, 'event_occurred')
    eventtransmitter.trigger.emit()
    assert hasattr(eventtransmitter, 'event_occurred')
