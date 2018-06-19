"""Utilities for keeping track of time in a task."""

from __future__ import division
from PyQt5 import QtCore
from axopy.messaging import Transmitter, TransmitterBase


class Counter(TransmitterBase):
    """Counts to a given number then transmits a timeout event.

    Parameters
    ----------
    max_count : int
        Number of iterations to go through before transmitting the `timeout`
        event. Must be greater than 1.
    reset_on_timeout : bool, optional
        Specifies whether or not the timer should reset its count back to zero
        once the timeout event occurs. The default behavior is to reset.

    Attributes
    ----------
    count : int
        Current count.
    timeout : Transmitter
        Transmitted when ``max_count`` has been reached.

    Examples
    --------
    Basic usage:

    >>> from axopy.timing import Counter
    >>> timer = Counter(2)
    >>> timer.increment()
    >>> timer.count
    1
    >>> timer.progress
    0.5
    >>> timer.increment()
    >>> timer.count
    0
    """

    timeout = Transmitter()

    def __init__(self, max_count=1, reset_on_timeout=True):
        super(Counter, self).__init__()
        max_count = int(max_count)
        if max_count < 1:
            raise ValueError('max_count must be > 1')

        self.reset_on_timeout = reset_on_timeout

        self.max_count = max_count
        self.count = 0

    @property
    def progress(self):
        """Progress toward timeout, from 0 to 1."""
        return self.count / self.max_count

    def increment(self):
        """Increment the counter.

        If `max_count` is reached, the ``timeout`` event is transmitted. If
        `reset_on_timeout` has been set to True (default), the timer is also
        reset.
        """
        self.count += 1

        if self.count == self.max_count:
            if self.reset_on_timeout:
                self.reset()

            self.timeout.emit()

    def reset(self):
        """Resets the count to 0 to start over."""
        self.count = 0


class Timer(TransmitterBase):
    """Real-time timer.

    Parameters
    ----------
    duration : int
        Duration of the timer in milliseconds.

    Attributes
    ----------
    timeout : Transmitter
        Transmitted when the timer has finished.
    """

    timeout = Transmitter()

    def __init__(self, duration):
        super(Timer, self).__init__()
        self.duration = duration

        self._qtimer = QtCore.QTimer()
        self._qtimer.setInterval(self.duration)
        self._qtimer.setSingleShot(True)
        self._qtimer.timeout.connect(self.timeout)

    def start(self):
        """Start the timer."""
        self._qtimer.start()

    def stop(self):
        """Stop the timer."""
        self._qtimer.stop()
