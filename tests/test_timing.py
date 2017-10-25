import pytest
from axopy.timing import IncrementalTimer


class TimeoutReceiver(object):

    def __init__(self):
        self.received = False

    def rx(self):
        self.received = True


def test_incremental_timer():
    timer = IncrementalTimer(2)
    recv = TimeoutReceiver()
    timer.timeout.connect(recv.rx)

    assert timer.count == 0

    timer.increment()
    assert not recv.received
    assert timer.count == 1
    assert timer.progress == 0.5
    timer.increment()
    assert recv.received
    assert timer.count == 0

    with pytest.raises(ValueError):
        IncrementalTimer(-1)
        IncrementalTimer(0)


def test_incremental_timer_float():
    timer = IncrementalTimer(3.5)
    recv = TimeoutReceiver()
    timer.timeout.connect(recv.rx)

    timer.increment()
    assert not recv.received
    timer.increment()
    timer.increment()
    assert recv.received


def test_incremental_timer_noreset():
    timer = IncrementalTimer(2, reset_on_timeout=False)

    assert timer.count == 0
    timer.increment()
    timer.increment()
    assert timer.count == 2
    timer.reset()
    assert timer.count == 0
