import pytest

from axopy.messaging import qt
from axopy import settings
settings.messaging_backend = qt.emitter

from axopy.messaging import emitter, receiver


class MemoryBlock(object):
    """Just remembers the last thing received."""

    def __init__(self):
        self.last_received = None

    @receiver
    def remember(self, data):
        self.last_received = data

@pytest.fixture
def memblock():
    return MemoryBlock()


class RelayBlock(object):
    """Just emits the data its emitter is called with."""

    @emitter(number=int)
    def relay(self, number):
        return number

@pytest.fixture
def relayblock():
    return RelayBlock()


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

@pytest.fixture
def complicatedblock():
    return ComplicatedBlock()


def test_emitter_connect(memblock, relayblock):
    # Ensure emitters support `connect` and disconnect
    relayblock.relay.connect(memblock.remember)
    relayblock.relay(4)
    assert memblock.last_received == 4

    relayblock.relay(8)
    assert memblock.last_received == 8

    relayblock.relay.disconnect(memblock.remember)
    relayblock.relay(9.0)
    assert memblock.last_received == 8


def test_receiver_connect(memblock, relayblock):
    # Ensure receivers support `connect` and `disconnect`
    memblock.remember.connect(relayblock.relay)
    relayblock.relay(2)
    assert memblock.last_received == 2

    memblock.remember.disconnect(relayblock.relay)
    relayblock.relay(9)
    assert memblock.last_received == 2


#@pytest.mark.skip(reason="Need to think more about this...")
def test_multidata(complicatedblock):
    # Ensure multiple things can be emitted at once
    complicatedblock.emitter.connect(complicatedblock.receiver)
    complicatedblock.emitter(4, (4.2, 2.8), 9.8)
    assert complicatedblock.coords == (4.2, 2.8)


message_with_suffix = None

@emitter(msg=str)
def emit_func():
    return 'message'

@receiver
def recv_func(msg):
    global message_with_suffix
    message_with_suffix = msg + 'suffix'

def test_emitter_receiver_functions():
    # Use functions (as opposed to methods) as emitters and receivers
    emit_func.connect(recv_func)
    assert emit_func() == 'message'
    assert message_with_suffix == 'messagesuffix'
