"""
Common processing tasks.
"""

import numpy as np
from scipy import signal

from .base import PipelineBlock


class Windower(PipelineBlock):
    """
    Takes new input data and combines with past data to maintain a sliding
    window with overlap. It is assumed that the input to this block has length
    (length-overlap).

    Parameters
    ----------
    length : int
        Total number of samples to output on each iteration.
    overlap : int, default=0
        Number of samples from previous input to keep in the current window.
    """

    def __init__(self, length, overlap=0):
        super(Windower, self).__init__()
        self.length = length
        self.overlap = overlap

        self.clear()

    def clear(self):
        self._out = None

    def process(self, data):
        if self._out is None:
            self._preallocate(data.shape[1])

        if self.overlap == 0:
            return data

        self._out[:self.overlap, :] = self._out[-self.overlap:, :]
        self._out[self.overlap:, :] = data

        return self._out.copy()

    def _preallocate(self, cols):
        self._out = np.zeros((self.length, cols))


class Filter(PipelineBlock):
    """
    Filters incoming data, accounting for initial conditions.

    Parameters
    ----------
    b : ndarray
        Numerator polynomial coefficients of the filter.
    a : ndarray, optional
        Denominator polynomial coefficients of the filter. Default is 1,
        meaning the filter is FIR.
    overlap : int, optional
        Number of samples overlapping in consecutive inputs. Needed for
        correct filter initial conditions in each filtering operation.
    """

    def __init__(self, b, a=1, overlap=0):
        super(Filter, self).__init__()
        self.b = b
        self.a = a
        self.overlap = overlap

        self.clear()

    def clear(self):
        self.x_prev = None
        self.y_prev = None

    def process(self, data):
        if self.x_prev is None:
            # first pass has no initial conditions
            out = signal.lfilter(
                self.b, self.a, data, axis=0)
        else:
            # subsequent passes get ICs from previous input/output
            num_ch = data.shape[1]
            K = max(len(self.a)-1, len(self.b)-1)
            self.zi = np.zeros((K, num_ch))
            # unfortunately we have to get zi channel by channel
            for c in range(data.shape[1]):
                self.zi[:, c] = signal.lfiltic(
                    self.b,
                    self.a,
                    self.y_prev[-(self.overlap+1)::-1, c],
                    self.x_prev[-(self.overlap+1)::-1, c])

            out, zf = signal.lfilter(
                self.b, self.a, data, axis=0, zi=self.zi)

        self.x_prev = data
        self.y_prev = out
        return out
