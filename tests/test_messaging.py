import importlib
import pytest

# need to import these initially so they can be reloaded in the blocks fixture
import messaging_blocks
import axopy.messaging.decorators


@pytest.fixture(params=['py', 'qt'])
def blocks(request):
    """Sets each messaging backends and yields the messaging_blocks module.

    The messaging_blocks module must be reloaded each time the backend is set
    so the @emitter and @receiver decorators work properly.
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


def test_emitter_connect(memblock, relayblock):
    """Ensure emitters support `connect` and disconnect."""
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
    """Ensure multiple things can be emitted at once."""
    complicatedblock.emitter.connect(complicatedblock.receiver)
    complicatedblock.emitter(4, (4.2, 2.8), 9.8)
    assert complicatedblock.coords == (4.2, 2.8)


def test_emitter_receiver_functions(blocks):
    """Use functions (as opposed to methods) as emitters and receivers."""
    blocks.emit_func.connect(blocks.recv_func)
    assert blocks.emit_func() == 'message'
    assert blocks.message_with_suffix == 'messagesuffix'
