# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:
"""Time-domain features.

Notation:
    - :math:`x_i` : value of a signal at time index :math:`i`
    - :math:`N` : length of the signal
"""

import numpy as np
from scipy.stats import skew as sp_skewness, kurtosis as sp_kurtosis

from axopy.features.util import (flatten_2d, check_output, rolling_window,
                                 inverted_t_window, trapezoidal_window)
from axopy.features.external.sample_entropy import sample_entropy_1d
from axopy.features.external.ar import autocorrelation, levinson


def mean_absolute_value(x, weights='mav', axis=-1, keepdims=False):
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
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
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
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        MAV of each channel.

    See Also
    --------
    axopy.features.util.inverted_t_window: Generates the window for MAV1
    axopy.features.util.trapezoidal_window: Generates the window for MAV2

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82-94, 1993.
    .. [2] A. Phinyomark, P. Phukpattaranont, and C.  Limsakul, "Feature
       Reduction and Selection for EMG Signal Classification," Expert Systems
       with Applications, vol. 39, no. 8, pp.  7420-7431, 2012.
    """
    n = x.shape[axis]

    if isinstance(weights, np.ndarray):
        w = weights
        if len(w) != n:
            raise ValueError("Number of weights in custom window function "
                             "does not match input size.")
    elif weights == 'mav':
        w = np.ones(n)
    elif weights == 'mav1':
        w = inverted_t_window(n, p=0.25, a=0.5)
    elif weights == 'mav2':
        w = trapezoidal_window(n, p=0.25)
    else:
        raise ValueError("Weights not recognized: should be 'mav', "
                         "'mav1', 'mav2', or a numpy array.")

    # reshape the window array so it multiplies along the correct axis
    # https://stackoverflow.com/a/30032182
    dims = np.ones(x.ndim, dtype=int)
    dims[axis] = -1
    w = w.reshape(dims)

    return np.mean(w * np.absolute(x), axis=axis, keepdims=keepdims)


def mean_value(x, axis=-1, keepdims=False):
    """Computes the mean value of each signal.

    .. math:: \\text{MV} = \\frac{1}{N} \\sum_{i=1}^{N} x_i

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        MV of each channel.
    """
    return np.mean(x, axis=axis, keepdims=keepdims)


def waveform_length(x, axis=-1, keepdims=False):
    """Computes the waveform length (WL) of each signal.

    Waveform length is the sum of the absolute value of the deltas between
    adjacent values (in time) of the signal:

    .. math:: \\text{WL} = \\sum_{i=1}^{N-1} | x_{i+1} - x_i |

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        WL of each channel.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82-94, 1993.
    """
    return np.sum(np.absolute(np.diff(x, axis=axis)),
                  axis=axis, keepdims=keepdims)


def wilson_amplitude(x, threshold=5e-6, axis=-1, keepdims=False):
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
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    threshold : float, optional
        The threshold used for the comparison between two consecutive samples.
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).

    Returns
    -------
    y : ndarray, shape (n_channels,)
        WAMP of each channel.

    References
    ----------
    .. [1] M. Zardoshti-Kermani, B. C. Wheeler, K. Badie, R. M. Hashemi, "EMG
        feature evaluation for movement control of upper extremity prostheses."
        IEEE Transactions on Rehabilitation Engineering, vol. 3, no. 4, p.p
        324-33, 1995.
    """
    return np.sum(np.abs(np.diff(x, n=1, axis=axis)) > threshold, axis=axis,
                  keepdims=keepdims)


def zero_crossings(x, threshold=0, axis=-1, keepdims=False):
    """Computes the number of zero crossings (ZC) of each signal.

    A zero crossing occurs when two adjacent values (in time) of the signal
    have opposite sign. A threshold is used to mitigate the effect of noise
    around zero. It is used as a measure of frequency information.

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    threshold : float, optional
        A threshold for discriminating true zero crossings from those caused
        by low-level noise situated about zero. By default, no threshold is
        used, so every sign change in the signal is counted.
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        ZC of each channel.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82-94, 1993.
    """
    # sum to count boolean values which indicate slope sign changes
    return np.sum(
        # two conditions:
        np.logical_and(
            # 1. sign changes from one sample to the next
            np.diff(np.signbit(x), axis=axis),
            # 2. difference between adjacent samples bigger than threshold
            np.absolute(np.diff(x, axis=axis)) > threshold),
        axis=axis,
        keepdims=keepdims)


def slope_sign_changes(x, threshold=0, axis=-1, keepdims=False):
    """Computes the number of slope sign changes (SSC) of each signal.

    A slope sign change occurs when the middle value of a group of three
    adjacent values in the signal is either greater than or less than both of
    the other two.

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    threshold : float, optional
        A threshold for discriminating true slope sign changes from those
        caused by low-level noise fluctuating about a specific value. By
        default, no threshold is used, so every slope sign change in the signal
        is counted.
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        SSC of each channel.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
       Multifunction Myoelectric Control," IEEE Transactions on Biomedical
       Engineering, vol. 40, no. 1, pp. 82-94, 1993.
    """
    diffs = np.diff(x, axis=axis)
    # transpose the diffs so rolling window works
    adj_diffs = rolling_window(np.swapaxes(np.absolute(diffs), -1, axis), 2)

    # sum to count boolean values which indicate slope sign changes
    return np.sum(
        # two conditions need to be met
        np.logical_and(
            # 1. sign of the diff changes from one pair of samples to the next
            np.diff(np.signbit(diffs), axis=axis),
            # 2. the max of two adjacent diffs is bigger than threshold
            # the transpose here is to un-transpose adj_diffs
            np.swapaxes(np.max(adj_diffs, axis=-1), -1, axis) > threshold),
        axis=axis, keepdims=keepdims)


def root_mean_square(x, axis=-1, keepdims=False):
    """Computes the root mean square of each signal.

    RMS is a commonly used feature for extracting amplitude information from
    physiological signals.

    .. math:: \\text{RMS} = \\sqrt{\\frac{1}{N} \\sum_{i=1}^N x_i^2}

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        RMS of each channel.
    """
    return np.sqrt(np.mean(np.square(x), axis=axis, keepdims=keepdims))


def integrated_emg(x, axis=-1, keepdims=False):
    """Sum over the rectified signal.

    .. math:: \\text{IEMG} = \\sum_{i=1}^{N} | x_{i} |

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        IEMG of each channel.
    """
    return np.sum(np.absolute(x), axis=axis, keepdims=keepdims)


def var(x, axis=-1, keepdims=False):
    """Variance of the signal.

    .. math::
        \\text{var} = \left( \\frac{1}{N}
            \\sum_{i=1}^{N} \\left(x_i - \\mu \\right)^2 \\right)

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        var of each channel.
    """
    return np.var(x, axis=axis, keepdims=keepdims)


def logvar(x, axis=-1, keepdims=False):
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

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        log-var of each channel.

    References
    ----------
    .. [1] J. M. Hahne, F. Bießmann, N. Jiang, H. Rehbaum, D. Farina, F. C.
       Meinecke, K.-R. Müller, and L. C. Parra, "Linear and Nonlinear
       Regression Techniques for Simultaneous and Proportional Myoelectric
       Control," IEEE Transactions on Neural Systems and Rehabilitation
       Engineering, vol. 22, no. 2, pp. 269–279, 2014.
    """
    return np.log10(np.var(x, axis=axis, keepdims=keepdims))


def skewness(x, bias=True, nan_policy='propagate', axis=-1,
             keepdims=False):
    """Skewness of the signal.

    .. math::
        \\text{Skewness} = \\frac{\\frac{1}{n} \\sum_{i=1}^n \\left( x_i-
            \\bar{x} \\right )^3}{\\left( \\frac{1}{n} \\sum_{i=1}^n
                \\left( x_i-\\bar{x} \\right )^2\\right )^\\frac{3}{2}}

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    bias : bool, optional
        If False, then the calculations are corrected for statistical bias.
    nan_policy : {'propagate', 'raise', 'omit'}, optional
        Defines how to handle when input contains nan. 'propagate' returns nan,
        'raise' throws an error, 'omit' performs the calculations ignoring nan
        values. Default is 'propagate'.
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        skewness of each channel.
    """
    skewness_ = sp_skewness(x, axis=axis, bias=bias,
                            nan_policy=nan_policy)
    return check_output(skewness_, axis=axis, keepdims=keepdims)


def kurtosis(x, fisher=True, bias=True, nan_policy='propagate', axis=-1,
             keepdims=False):
    """Kurtosis of the signal.

    .. math::
        \\text{Kurtosis} = \\frac{\\frac{1}{n} \\sum_{i=1}^n \\left( x_i-
            \\bar{x} \\right )^4}{\\left( \\frac{1}{n} \\sum_{i=1}^n
                \\left( x_i-\\bar{x} \\right )^2\\right )^2} - 3

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    fisher : bool, optional
        If True, Fisher's definition is used (normal ==> 0.0). If False,
        Pearson's definition is used (normal ==> 3.0).
    bias : bool, optional
        If False, then the calculations are corrected for statistical bias.
    nan_policy : {'propagate', 'raise', 'omit'}, optional
        Defines how to handle when input contains nan. 'propagate' returns nan,
        'raise' throws an error, 'omit' performs the calculations ignoring nan
        values. Default is 'propagate'.
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    -------
    y : ndarray, shape (n_channels,)
        kurtosis of each channel.
    """
    kurtosis_ = sp_kurtosis(x, axis=axis, fisher=fisher, bias=bias,
                            nan_policy=nan_policy)
    return check_output(kurtosis_, axis=axis, keepdims=keepdims)


def ar(x, order, axis=-1, keepdims=False):
    """Auto-regressive (linear prediction filter) coefficients.

    .. math::
        x_n = \\sum_{i=1}^p a_i x_{n-i}

    .. math::
        \text{AR} = [a_1 \\ldots a_p]

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    order : int
        Order (p) of the autoregressive linear process.
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. If True and
        ``order`` > 1, the output will have one more dimension than the input.

    Returns
    -------
    y : ndarray, shape (n_channels, order) or (order, n_channels)
        The AR coefficients. The shape of the output will be determined by the
        input format. If x has shape (n_channels, n_samples), then the output
        shape will be (n_channels, order), otherwise it will be
        (order, n_channels).
    """

    R = autocorrelation(x, axis=axis)
    ar_ = np.apply_along_axis(levinson, axis=axis, arr=R, order=order,
                              allow_singularity=False)
    ar_ = flatten_2d(ar_, axis=axis)
    return check_output(ar_, axis=axis, keepdims=keepdims)


def sample_entropy(x, m=2, r=None, delta=1, axis=-1, keepdims=False):
    """
    Multiscale sample entropy.

    Parameters
    ----------
    x : array
        Input data. Use the ``axis`` argument to specify the "time axis".
    m : int, optional
        Embedding dimension. Default is 2.
    r : float, optional
        Tolerance level. Default is 0.2 * np.std(x).
    delta : int, optional
        Skipping parameter (downsampling factor). Default is 1, which
        corresponds to no skipping.
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. That is, if the
        input is 2D, the output will be 2D even if a dimension collapses to
        size 1.

    Returns
    ------
    y : array
        Sample entropy of each channel.

    References
    ----------
    .. [1] J. S. Richman, J. R. Moorman, "Physiological time-series analysis
        using approximate entropy and sample entropy," American Journal of
        Physiology-Heart and Circulatory Physiology, vol. 278, no. 6, pp.
        H2039--H2049, 2000.
    """
    if r is None:
        r = 0.2 * np.std(x)

    samp_en = np.apply_along_axis(sample_entropy_1d, axis=axis, arr=x, m=m, r=r,
                                  delta=delta)

    return check_output(samp_en, axis=axis, keepdims=keepdims)


def hjorth(x, axis=-1, keepdims=False):
    """Computes the Hjorth parameters.

    The following Hjorth parameters are computed: Activity, Mobility, and
    Complexity.

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. If True, the
        output will have one more dimension than the input.

    Returns
    -------
    y : ndarray, shape (n_channels, 3) or (3, n_channels)
        The Hjorth parameters are returned in the following order: Activity,
        Mobility, and Complexity. The shape of the output will be determined by
        the input format. If x has shape (n_channels, n_samples), then the
        output shape will be (n_channels, 3), otherwise it will be
        (3, n_channels).

    References
    ----------
    .. [1] B. Hjorth, "EEG analysis based on time domain properties,"
      Electroencephalography and clinical neurophysiology, vol. 29, no. 3, pp.
      306-310, 1970.
    """
    activity = [np.var(x_, axis=axis, keepdims=True).reshape(-1,) for x_ in
                [np.diff(x, i, axis=axis) for i in range(3)]]
    mobility = [np.sqrt(activity[i+1] / activity[i]).reshape(-1,) for i in
                range(2)]
    complexity = mobility[1] / mobility[0]
    hjorth_ = np.concatenate((activity[0], mobility[0], complexity))
    return check_output(hjorth_, axis, keepdims=keepdims)


def histogram(x, bins, axis=-1, keepdims=False):
    """Computes the histogram of the signal.

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    bins : int or sequence of scalars or str, optional
        If ``bins`` is an int, it defines the number of equal-width
        bins in the given range. If ``bins`` is a sequence, it defines the bin
        edges, including the rightmost edge, allowing for non-uniform bin
        widths.
    axis : int, optional
        The axis to compute the feature along. By default, it is computed along
        rows, so the input is assumed to be shape (n_channels, n_samples).
    keepdims : bool, optional
        Whether or not to keep the dimensionality of the input. If True, the
        output will have one more dimension than the input.

    Returns
    -------
    y : ndarray, shape (n_channels, bins) or (bins, n_channels)
        The shape of the output will be determined by the input format. If x
        has shape (n_channels, n_samples), then the output shape will be
        (n_channels, bins), otherwise it will be (bins, n_channels).
    """
    # numpy histogram returns counts and edges but we only need the counts
    hist = np.apply_along_axis(lambda x: np.histogram(x, bins)[0], axis=axis,
                               arr=x)
    hist = flatten_2d(hist, axis=axis)
    return check_output(hist, axis=axis, keepdims=keepdims)
