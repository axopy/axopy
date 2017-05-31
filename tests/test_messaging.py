import sys
import importlib
import pytest

# need to import these initially so they can be reloaded in the blocks fixture
import messaging_blocks
import axopy.messaging.decorators


@pytest.fixture(params=['py', 'qt'])
def blocks(request):
    """Sets each messaging backends and yields the messaging_blocks module.

    The messaging_blocks module must be reloaded each time the backend is set
    so the @transmitter and @receiver decorators work properly.
    """
    from axopy import settings
    settings.messaging_backend = request.param

    # need to reload to actually see the backend change
    importlib.reload(axopy.messaging.decorators)
    importlib.reload(messaging_blocks)
    yield messaging_blocks


@pytest.fixture
def memblock(blocks):
    return blocks.MemoryBlock()


@pytest.fixture
def relayblock(blocks):
    return blocks.RelayBlock()


@pytest.fixture
def complicatedblock(blocks):
    return blocks.ComplicatedBlock()


@pytest.fixture
def chainedtransmitters(blocks):
    return blocks.ChainedTransmittersBlock()


@pytest.fixture
def eventtransmitter(blocks):
    return blocks.EventTransmitterBlock()


def test_transmitter_connect(memblock, relayblock):
    """Ensure transmitters support `connect` and disconnect."""
    relayblock.relay.connect(memblock.remember)
    relayblock.relay(4)
    assert memblock.last_received == 4

    relayblock.relay(8)
    assert memblock.last_received == 8

    relayblock.relay.disconnect(memblock.remember)
    relayblock.relay(9.0)
    assert memblock.last_received == 8


def test_receiver_connect(memblock, relayblock):
    """Ensure receivers support `connect` and `disconnect`."""
    memblock.remember.connect(relayblock.relay)
    relayblock.relay(2)
    assert memblock.last_received == 2

    memblock.remember.disconnect(relayblock.relay)
    relayblock.relay(9)
    assert memblock.last_received == 2


def test_multidata(complicatedblock):
    """Ensure multiple things can be transmitted at once."""
    # transmitter data format specified as tuples
    complicatedblock.tuple_transmitter.connect(complicatedblock.set_coords)
    complicatedblock.tuple_transmitter(4, (2.1, 6.2), 42.1)
    assert complicatedblock.coords == (2.1, 6.2)


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="kwarg transmitter format requires Python 3.6+")
def test_transmitter_formats(complicatedblock):
    """Ensure newer data formats work for Python 3.6+."""
    # transmitter data format specified as multiple kwargs
    complicatedblock.dict_transmitter.connect(complicatedblock.set_coords)
    complicatedblock.dict_transmitter(4, (4.2, 2.8), 9.8)
    assert complicatedblock.coords == (4.2, 2.8)

    # transmitter data format specified with mixture of args and kwargs
    complicatedblock.mixed_transmitter.connect(complicatedblock.set_coords)
    complicatedblock.mixed_transmitter(1, (7.1, 2.4), 59.1)
    assert complicatedblock.coords == (7.1, 2.4)


def test_transmitter_receiver_functions(blocks):
    """Use functions (as opposed to methods) as transmitters and receivers."""
    blocks.transmit_func.connect(blocks.recv_func)
    assert blocks.transmit_func() == 'message'
    assert blocks.message_with_suffix == 'messagesuffix'


def test_chained_transmitters(chainedtransmitters):
    """Chain transmitters together, call the first, then check the end result."""
    chainedtransmitters.start.connect(chainedtransmitters.intermediate)
    chainedtransmitters.intermediate.connect(chainedtransmitters.finish)
    chainedtransmitters.start("hey")
    assert chainedtransmitters.message == "heytouchedoncetouchedtwice"


def test_empty_transmitter(eventtransmitter):
    eventtransmitter.trigger.connect(eventtransmitter.on_event)
    assert not hasattr(eventtransmitter, 'event_occurred')
    eventtransmitter.trigger()
    assert hasattr(eventtransmitter, 'event_occurred')
