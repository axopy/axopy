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

    timer.increment()
    assert recv.received == False
    timer.increment()
    assert recv.received == True

    with pytest.raises(ValueError):
        IncrementalTimer(-1)
        IncrementalTimer(0)


def test_incremental_timer_float():
    timer = IncrementalTimer(3.5)
    recv = TimeoutReceiver()
    timer.timeout.connect(recv.rx)

    timer.increment()
    assert recv.received == False
    timer.increment()
    timer.increment()
    assert recv.received == True
