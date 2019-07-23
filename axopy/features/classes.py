from abc import ABC, abstractmethod

from axopy.features.time import (mean_absolute_value, mean_value,
                                 waveform_length, wilson_amplitude,
                                 zero_crossings, slope_sign_changes,
                                 root_mean_square, integrated_emg, var, logvar,
                                 skewness, kurtosis, ar, sample_entropy,
                                 hjorth, histogram)


class _FeatureBase(ABC):
    """Generic interface for feature extraction.

    Every derived class is required to implement a ``compute`` method.

    Warning: this is a base class which should not be used directly. Use
    derived classes instead.

    Parameters
    ----------
    features_per_channel : int
        Extracted features per channel.
    """

    def __init__(self, features_per_channel):
        super().__init__()
        self.features_per_channel = features_per_channel

    @abstractmethod
    def compute(self, x):
        pass


class MeanAbsoluteValue(_FeatureBase):
    """Computes the mean absolute value (MAV) of each signal.

    Mean absolute value is a popular feature for obtaining amplitude
    information from EMG, especially in gesture classification contexts [1]_.

    There is an optional windowing function applied to the rectified signal,
    described as MAV1 and MAV2 in some references. A custom window can also be
    used. The general definition is given as:

    .. math:: \\text{MAV} = \\frac{1}{N} \\sum_{i=1}^{N} w_i |x_i|

    Normal MAV does not use a windowing function, equivalent to setting all
    :math:`w_i = 1`.

    MAV1 refers to a rectangular window which de-emphasizes the beginning and
    ending of an input window. The first quarter of the input samples receive
    a weight of 0.5, the middle half of the input samples receive a weight of
    1, and the final quarter recieves a weight of 0.5:

    .. math::
       w_i =
       \\begin{cases}
           1,   & \\frac{N}{4} \\leq i \\leq \\frac{3N}{4} \\\\
           0.5, & \\text{otherwise}
       \\end{cases}

    MAV2 uses a similar window structure to MAV1 (i.e. broken into first
    quarter, middle half, and final quarter), but the window is trapezoidal
    in shape, ramping from 0 to 1 over the first quarter and from 1 to 0 over
    the last quarter:

    .. math::
       w_i =
       \\begin{cases}
           1, & \\frac{N}{4} \\leq i \\leq \\frac{3N}{4} \\\\
           \\frac{4i}{N}, & i < \\frac{N}{4} \\\\
           \\frac{4(i - N)}{N}, & i > \\frac{3N}{4}
       \\end{cases}

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
       Engineering, vol. 40, no. 1, pp. 82-94, 1993.
    .. [2] A. Phinyomark, P. Phukpattaranont, and C.  Limsakul, "Feature
       Reduction and Selection for EMG Signal Classification," Expert Systems
       with Applications, vol. 39, no. 8, pp.  7420-7431, 2012.
    """

    def __init__(self, weights='mav'):
        super().__init__(features_per_channel=1)
        self.weights = weights

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return mean_absolute_value(
            x=data,
            weights=self.weights,
            axis=-1,
            keepdims=False)


class MeanValue(_FeatureBase):
    """Computes the mean value of each signal.

    .. math:: \\text{MV} = \\frac{1}{N} \\sum_{i=1}^{N} x_i
    """

    def __init__(self):
        super().__init__(features_per_channel=1)

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return mean_value(
            x=data,
            axis=-1,
            keepdims=False)


class WaveformLength(_FeatureBase):
    """Computes the waveform length (WL) of each signal.

    Waveform length is the sum of the absolute value of the deltas between
    adjacent values (in time) of the signal:

    .. math:: \\text{WL} = \\sum_{i=1}^{N-1} | x_{i+1} - x_i |

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82-94, 1993.
    """

    def __init__(self):
        super().__init__(features_per_channel=1)

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return waveform_length(
            x=data,
            axis=-1,
            keepdims=False)


class WilsonAmplitude(_FeatureBase):
    """Computes the Wilson amplitude of each signal.

    The Wilson amplitude is the number of counts for each change in the EMG
    signal amplitude that exceeds a predefined threshold.

    .. math:: \\text{WAMP} = \sum_{i=1}^{N-1} f\left( \left| x_{i+1} -
        x_i \right| \right)

    .. math::
       f\left(x\right) =
       \begin{cases}
            1, \text{if } x \geq \text{threshold},\\
                0, \text{ otherwise}
        \end{cases}

    Parameters
    ----------
    threshold : float, optional
        The threshold used for the comparison between two consecutive samples.
        Default is 5e-6.

    References
    ----------
    .. [1] M. Zardoshti-Kermani, B. C. Wheeler, K. Badie, R. M. Hashemi, "EMG
        feature evaluation for movement control of upper extremity prostheses."
        IEEE Transactions on Rehabilitation Engineering, vol. 3, no. 4, p.p
        324-33, 1995.
    """

    def __init__(self, threshold=5e-6):
        super().__init__(features_per_channel=1)
        self.threshold = threshold

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return wilson_amplitude(
            x=data,
            threshold=self.threshold,
            axis=-1,
            keepdims=False)


class ZeroCrossing(_FeatureBase):
    """Computes the number of zero crossings (ZC) of each signal.

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
       Engineering, vol. 40, no. 1, pp. 82-94, 1993.
    """

    def __init__(self, threshold=0.):
        super().__init__(features_per_channel=1)
        self.threshold = threshold

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return zero_crossings(
            x=data,
            threshold=self.threshold,
            axis=-1,
            keepdims=False)


class SlopeSignChanges(_FeatureBase):
    """Computes the number of slope sign changes (SSC) of each signal.

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
       Engineering, vol. 40, no. 1, pp. 82-94, 1993.
    """

    def __init__(self, threshold=0.):
        super().__init__(features_per_channel=1)
        self.threshold = threshold

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return slope_sign_changes(
            x=data,
            threshold=self.threshold,
            axis=-1,
            keepdims=False)


class RootMeanSquare(_FeatureBase):
    """Computes the root mean square of each signal.

    RMS is a commonly used feature for extracting amplitude information from
    physiological signals.

    .. math:: \\text{RMS} = \\sqrt{\\frac{1}{N} \\sum_{i=1}^N x_i^2}
    """

    def __init__(self):
        super().__init__(features_per_channel=1)

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return root_mean_square(
            x=data,
            axis=-1,
            keepdims=False)


class IntegratedEMG(_FeatureBase):
    """Sum over the rectified signal.

    .. math:: \\text{IEMG} = \\sum_{i=1}^{N} | x_{i} |
    """

    def __init__(self):
        super().__init__(features_per_channel=1)

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return integrated_emg(
            x=data,
            axis=-1,
            keepdims=False)


class Var(_FeatureBase):
    """Variance of the signal.

    .. math::
        \\text{var} = \left( \\frac{1}{N}
            \\sum_{i=1}^{N} \\left(x_i - \\mu \\right)^2 \\right)
    """

    def __init__(self):
        super().__init__(features_per_channel=1)

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return var(
            x=data,
            axis=-1,
            keepdims=False)


class LogVar(_FeatureBase):
    """Log of the variance of the signal.

    .. math::
        \\text{log-var} = \\log \left( \\frac{1}{N}
            \\sum_{i=1}^{N} \\left(x_i - \\mu \\right)^2 \\right)

    For electrophysiological signals that are mean-zero, this is the log of the
    mean square value, making it similar to :func:`root_mean_square` but
    scaling differently (slower) with :math:`x`.

    For EMG data recorded from forearm muscles, log-var has been found to
    relate to wrist angle fairly linearly [1]_.

    Note: base-10 logarithm is used, though the base is not specified in [1]_.

    References
    ----------
    .. [1] J. M. Hahne, F. Bießmann, N. Jiang, H. Rehbaum, D. Farina, F. C.
       Meinecke, K.-R. Müller, and L. C. Parra, "Linear and Nonlinear
       Regression Techniques for Simultaneous and Proportional Myoelectric
       Control," IEEE Transactions on Neural Systems and Rehabilitation
       Engineering, vol. 22, no. 2, pp. 269–279, 2014.
    """

    def __init__(self):
        super().__init__(features_per_channel=1)

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return logvar(
            x=data,
            axis=-1,
            keepdims=False)


class Skewness(_FeatureBase):
    """Skewness of the signal.

    .. math::
        \\text{Skewness} = \\frac{\\frac{1}{n} \\sum_{i=1}^n \\left( x_i-
            \\bar{x} \\right )^3}{\\left( \\frac{1}{n} \\sum_{i=1}^n
                \\left( x_i-\\bar{x} \\right )^2\\right )^\\frac{3}{2}}

    Parameters
    ----------
    bias : bool, optional
        If False, then the calculations are corrected for statistical bias.
    nan_policy : {'propagate', 'raise', 'omit'}, optional
        Defines how to handle when input contains nan. 'propagate' returns nan,
        'raise' throws an error, 'omit' performs the calculations ignoring nan
        values. Default is 'propagate'.
    """

    def __init__(self, bias=True, nan_policy='propagate'):
        super().__init__(features_per_channel=1)
        self.bias = bias
        self.nan_policy = nan_policy

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return skewness(
            x=data,
            bias=self.bias,
            nan_policy=self.nan_policy,
            axis=-1,
            keepdims=False)


class Kurtosis(_FeatureBase):
    """Kurtosis of the signal.

    .. math::
        \\text{Kurtosis} = \\frac{\\frac{1}{n} \\sum_{i=1}^n \\left( x_i-
            \\bar{x} \\right )^4}{\\left( \\frac{1}{n} \\sum_{i=1}^n
                \\left( x_i-\\bar{x} \\right )^2\\right )^2} - 3

    Parameters
    ----------
    fisher : bool, optional
        If True, Fisher's definition is used (normal ==> 0.0). If False,
        Pearson's definition is used (normal ==> 3.0).
    bias : bool, optional
        If False, then the calculations are corrected for statistical bias.
    nan_policy : {'propagate', 'raise', 'omit'}, optional
        Defines how to handle when input contains nan. 'propagate' returns nan,
        'raise' throws an error, 'omit' performs the calculations ignoring nan
        values. Default is 'propagate'.
    """

    def __init__(self, fisher=True, bias=True, nan_policy='propagate'):
        super().__init__(features_per_channel=1)
        self.fisher = fisher
        self.bias = bias
        self.nan_policy = nan_policy

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return kurtosis(
            x=data,
            fisher=self.fisher,
            bias=self.bias,
            nan_policy=self.nan_policy,
            axis=-1,
            keepdims=False)


class AR(_FeatureBase):
    """Auto-regressive (linear prediction filter) coefficients.

    .. math::
        x_n = \\sum_{i=1}^p a_i x_{n-i}

    .. math::
        \text{AR} = [a_1 \\ldots a_p]

    Parameters
    ----------
    order : int, optional
        Order (p) of the autoregressive linear process. Default is 3.
    """

    def __init__(self, order=3):
        super().__init__(features_per_channel=order)
        self.order = order

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (order * n_channels,)
            Output data.
        """
        return ar(
            x=data,
            order=self.order,
            axis=-1,
            keepdims=False)


class SampleEntropy(_FeatureBase):
    """
    Multiscale sample entropy.

    Parameters
    ----------
    m : int, optional
        Embedding dimension. Default is 2.
    r : float, optional
        Tolerance level. Default is 0.2 * np.std(x).
    delta : int, optional
        Skipping parameter (downsampling factor). Default is 1, which
        corresponds to no skipping.

    References
    ----------
    .. [1] J. S. Richman, J. R. Moorman, "Physiological time-series analysis
        using approximate entropy and sample entropy," American Journal of
        Physiology-Heart and Circulatory Physiology, vol. 278, no. 6, pp.
        H2039--H2049, 2000.
    """

    def __init__(self, m=2, r=None, delta=1):
        super().__init__(features_per_channel=1)
        self.m = m
        self.r = r
        self.delta = delta

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_channels,)
            Output data.
        """
        return sample_entropy(
            x=data,
            m=self.m,
            r=self.r,
            delta=self.delta,
            axis=-1,
            keepdims=False)


class Hjorth(_FeatureBase):
    """Computes the Hjorth parameters.

    The following Hjorth parameters are computed: Activity, Mobility, and
    Complexity.

    References
    ----------
    .. [1] B. Hjorth, "EEG analysis based on time domain properties,"
      Electroencephalography and clinical neurophysiology, vol. 29, no. 3, pp.
      306-310, 1970.
    """

    def __init__(self):
        super().__init__(features_per_channel=3)

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (3 * n_channels,)
            Output data.
        """
        return hjorth(
            x=data,
            axis=-1,
            keepdims=False)


class Histogram(_FeatureBase):
    """Computes the histogram of the signal.

    Parameters
    ----------
    bins : int, optional
        Defines the number of equal-width bins in the given range. Default is
        10.
    """

    def __init__(self, bins=10):
        super().__init__(features_per_channel=bins)
        self.bins = bins

    def compute(self, data):
        """
        Computes the features.

        Parameters
        ----------
        x : ndarray, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        y : ndarray, shape (bins * n_channels,)
            Output data.
        """
        return histogram(
            x=data,
            bins=self.bins,
            axis=-1,
            keepdims=False)
