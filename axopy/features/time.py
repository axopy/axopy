"""
Time-domain features.

Notation:
    - :math:`x_i` : value of a signal at time index :math:`i`
    - :math:`N` : length of the signal
"""

import numpy as np
from .base import Feature
from ..util import ensure_2d, rolling_window


class MAV(Feature):
    r"""Computes the mean absolute value of each signal.

    Mean absolute value is a popular feature for obtaining amplitude
    information from EMG, especially in gesture classification contexts.

    There is an optional windowing function applied to the rectified signal,
    described as MAV1 and MAV2 in some references. A custom window can also be
    used. The general definition is given as:

    .. math:: \text{MAV} = \frac{1}{N} \sum_{i=1}^{N} w_i |x_i|

    Normal MAV does not use a windowing function, equivalent to setting all
    :math:`w_i = 1`.

    MAV1 refers to a rectangular window which de-emphasizes the beginning and
    ending of an input window. The first quarter of the input samples receive
    a weight of 0.5, the middle half of the input samples receive a weight of
    1, and the final quarter recieves a weight of 0.5:

    .. math::
        w_i =
        \begin{cases}
            1,   & \frac{N}{4} \leq i \leq \frac{3N}{4} \\
            0.5, & \text{otherwise}
        \end{cases}

    MAV2 uses a similar window structure to MAV1 (i.e. broken into first
    quarter, middle half, and final quarter), but the window is trapezoidal
    in shape, ramping from 0 to 1 over the first quarter and from 1 to 0 over
    the last quarter:

    .. math::
        w_i =
        \begin{cases}
            1, & \frac{N}{4} \leq i \leq \frac{3N}{4} \\
            \frac{4i}{N}, & i < \frac{N}{4} \\
            \frac{4(N - i)}{N}, & i > \frac{3N}{4}
        \end{cases}

    Parameters
    ----------
    weights : str or ndarray, optional
        Weights to use. Possible values:

            - 'mav' : all samples in the signal are weighted equally (default).
            - 'mav1' : rectangular window with the middle half of the signal
              receiving unit weight and the first and last quarters of the
              signal receiving half weight.
            - 'mav2' : similar to 'mav1', but weights on the first and last
              quarters increase and decrease between 0 and 1 respectively,
              forming a trapezoidal window.
            - [ndarray] : user-supplied weights to apply. Must be a 1D array
              with the same length as the signals received in the ``compute``
              method.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82–94, 1993.
    .. [2] A. Phinyomark, P. Phukpattaranont, and C. Limsakul, "Feature
       Reduction and Selection for EMG Signal Classification," Expert Systems
       with Applications, vol. 39, no. 8, pp. 7420-7431, 2012.
    """

    def __init__(self, weights='mav'):
        self.weights = weights

        self._n = 0

    def compute(self, x):
        x = ensure_2d(x)

        n = x.shape[1]
        if n != self._n:
            self._n = n
            self._init_weights()

        return np.mean(self._w * np.absolute(x), axis=1)

    def _init_weights(self):
        if self.weights == 'mav':
            # unit weights
            self._w = np.ones(self._n)
        elif self.weights == 'mav1':
            # rectangular window de-emphasizing first and last quarters
            self._w = np.ones(self._n)
            self._w[:int(np.ceil(0.25 * self._n)) - 1] = 0.5
            self._w[int(np.floor(0.75 * self._n)):] = 0.5
        elif self.weights == 'mav2':
            # trapezoidal window de-emphasizing first and last quarters
            self._w = np.ones(self._n)
            r1 = np.arange(0, int(np.ceil(0.25 * self._n)) - 1)
            r2 = np.arange(int(np.floor(0.75 * self._n)), self._n)
            self._w[r1] = 4 * (r1 + 1) / self._n
            self._w[r2] = 4 * (self._n - (r2 + 1)) / self._n
        elif isinstance(self.weights, np.ndarray):
            self._w = self.weights
            if len(self._w) != self._n:
                raise ValueError("Number of weights in custom window function "
                                 "does not match input size.")
        else:
            raise ValueError("Weights not recognized: should be 'mav', "
                             "'mav1', 'mav2', or a numpy array.")


class WL(Feature):
    r"""Computes the waveform length of each signal.

    Waveform length is the sum of the absolute value of the deltas between
    adjacent values (in time) of the signal:

    .. math:: \text{WL} = \sum_{i=1}^{N-1} | x_{i+1} - x_i |

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82–94, 1993.
    """

    def compute(self, x):
        x = ensure_2d(x)
        return np.sum(np.absolute(np.diff(x, axis=1)), axis=1)


class ZC(Feature):
    """Computes the number of zero crossings of each signal.

    A zero crossing occurs when two adjacent values (in time) of the signal
    have opposite sign. A threshold is used to mitigate the effect of noise
    around zero. It is used as a measure of frequency information.

    Parameters
    ----------
    threshold : float, optional
        A threshold for discriminating true zero crossings from those caused
        by low-level noise situated about zero. By default, no threshold is
        used, so every sign change in the signal is counted.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82–94, 1993.
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

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82–94, 1993.
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


class RMS(Feature):
    r"""Computes the root mean square of each signal.

    RMS is a commonly used feature for extracting amplitude information from
    physiological signals.

    .. math:: \text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^N x_i^2}
    """

    def compute(self, x):
        x = ensure_2d(x)
        return np.sqrt(np.mean(np.square(x), axis=1))
