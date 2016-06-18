"""
Time-domain features.
"""

import numpy as np
from .base import Feature
from ..util import ensure_2d, rolling_window


class MAV(Feature):
    """
    Computes the mean absolute value of each signal.

    Literally the mean of the absolute value of the signal.
    """

    def compute(self, x):
        x = ensure_2d(x)
        return np.mean(np.absolute(x), axis=1)


class WL(Feature):
    """Computes the waveform length of each signal.

    Waveform length is the sum of the absolute value of the deltas between
    adjacent values (in time) of the signal.
    """

    def compute(self, x):
        x = ensure_2d(x)
        return np.sum(np.absolute(np.diff(x, axis=1)), axis=1)


class ZC(Feature):
    """Computes the number of zero crossings of each signal.

    A zero crossing occurs when two adjacent values (in time) of the signal
    have opposite sign.

    Parameters
    ----------
    threshold : float, optional
        A threshold for discriminating true zero crossings from those caused
        by low-level noise situated about zero. By default, no threshold is
        used, so every sign change in the signal is counted.
    """

    def __init__(self, threshold=0):
        self.threshold = threshold

    def compute(self, x):
        x = ensure_2d(x)
        # two conditions:
        #   1. sign changes from one sample to the next
        #   2. difference between adjacent samples bigger than threshold
        return np.sum(
            np.logical_and(
                np.diff(np.signbit(x), axis=1),
                np.absolute(np.diff(x, axis=1)) > self.threshold),
            axis=1)


class SSC(Feature):
    """Computes the number of slope sign changes of each signal.

    A slope sign change occurs when the middle value of a group of three
    adjacent values in the signal is either greater than or less than both of
    the other two.

    Parameters
    ----------
    threshold : float, optional
        A threshold for discriminating true slope sign changes from those
        caused by low-level noise fluctuating about a specific value. By
        default, no threshold is used, so every slope sign change in the signal
        is counted.
    """

    def __init__(self, threshold=0):
        self.threshold = threshold

    def compute(self, x):
        x = ensure_2d(x)
        # two conditions:
        #   1. sign of the diff changes from one pair of samples to the next
        #   2. the max of two adjacent diffs is bigger than threshold
        return np.sum(
            np.logical_and(
                np.diff(np.signbit(np.diff(x, axis=1)), axis=1),
                np.max(rolling_window(
                    np.absolute(
                        np.diff(x, axis=1)), 2), axis=-1) > self.threshold),
            axis=1)
