"""Utilities for keeping track of time in a task."""

from __future__ import division
from PyQt5 import QtCore
from axopy.messaging import transmitter, receiver


class Counter(object):
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

    Examples
    --------
    Basic usage:

    >>> from axopy.timing import Counter
    >>> timer = Counter(2)
    >>> timer.timeout.connect(lambda: print("timed out"))
    >>> timer.increment()
    >>> timer.count
    1
    >>> timer.progress
    0.5
    >>> timer.increment()
    timed out
    >>> timer.count
    0
    """

    def __init__(self, max_count=1, reset_on_timeout=True):
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

    @receiver
    def increment(self):
        """Increment the counter.

        If `max_count` is reached, the `timeout` event is transmitted. If
        `reset_on_timeout` has been set to True (default), the timer is also
        reset.
        """
        self.count += 1

        if self.count == self.max_count:
            if self.reset_on_timeout:
                self.reset()

            self.timeout()

    @transmitter()
    def timeout(self):
        """Transmitted when `max_count` is reached."""
        return

    def reset(self):
        """Resets the count to 0 to start over."""
        self.count = 0


class Timer(object):

    def __init__(self, duration):
        self.duration = duration

        self._qtimer = QtCore.QTimer()
        self._qtimer.setInterval(self.duration)
        self._qtimer.setSingleShot(True)
        self._qtimer.timeout.connect(self.timeout)

    def start(self):
        self._qtimer.start()

    def stop(self):
        self._qtimer.stop()

    @transmitter()
    def timeout(self):
        return
