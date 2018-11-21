"""Utility functions."""

import numpy as np


def shape_output(array, axis, keepdims):
    """Make sure the output has the desired type and shape. Scalar outputs
    will be converted into numpy.float64. The ``keepdims`` parameter
    determines whether the array will be expanded along the given axis. This
    function is useful when features have been computed by calling functions
    that implicitly reduce the dimensionality (e.g. numpy.apply_along_axis).

    Parameters
    ----------
    array : array or float
        The array with the computed feature.
    axis : int
        The axis along which the feature has been computed.
    keepdims : bool
        When True the dimensionality of the input will be retained by expanding
        the output.

    Returns
    -------
    out : array
    """
    if keepdims is False:
        # For a scalar ouput make sure it is returned as np.float64
        return np.float64(array)
    else:
        return np.expand_dims(array, axis)


def ensure_2d(array):
    """Make sure an array has at least 2 dimensions.

    Useful for handling arrays with ``shape=(n,)`` when you want ``(1, n)``.

    Parameters
    ----------
    array : array, shape (n,)
        The input array. If 2-dimensional, nothing is done.

    Returns
    -------
    array : array, shape (1, n)
        The input array as a "row vector".
    """
    if array.ndim == 1:
        array = np.atleast_2d(array)
    return array


def rolling_window(array, n):
    """Create a rolling window from an array.

    An extra axis is added to efficiently compute statistics over. Use
    ``axis=-1`` to remove the extra axis.

    Parameters
    ----------
    array : ndarray
        The input array.
    n : int
        Window length.

    Returns
    -------
    window : array
        The length-n windows of the input array.

    Examples
    --------
    >>> import numpy as np
    >>> from axopy.features.util import rolling_window
    >>> x = np.array([1, 2, 3, 4, 5])
    >>> rolling_window(x, 2)
    array([[1, 2],
           [2, 3],
           [3, 4],
           [4, 5]])
    >>> rolling_window(x, 3)
    array([[1, 2, 3],
           [2, 3, 4],
           [3, 4, 5]])
    >>> x = np.array([[1, 2, 3, 4], [5, 6, 7, 8]])
    >>> rolling_window(x, 2)
    array([[[1, 2],
            [2, 3],
            [3, 4]],
    <BLANKLINE>
           [[5, 6],
            [6, 7],
            [7, 8]]])

    References
    ----------
    .. [1] https://mail.scipy.org/pipermail/numpy-discussion/2010-December/054392.html # noqa
    """
    shape = array.shape[:-1] + (array.shape[-1] - n + 1, n)
    strides = array.strides + (array.strides[-1],)
    return np.lib.stride_tricks.as_strided(array,
                                           shape=shape,
                                           strides=strides)


def inverted_t_window(n, p=0.25, a=0.5):
    """Generate a rectangular window with de-emphasized onset and offset.

    The middle portion of the window is unity, while the onset and offset are
    flat with less weight, making an inverted "T" shape.

    .. math::
       w_i =
       \\begin{cases}
           1,   & pn \\leq i \\leq (1-p)n \\\\
           a, & \\text{otherwise}
       \\end{cases}

    Parameters
    ----------
    n : int
        Number of window samples to generate.
    p : float, optional
        Proportion of the window to consider as "onset" and "offset". Should be
        less than 0.5.
    a : float, optional
        Window value during the onset and offset portions. Should be less than
        one.

    Returns
    -------
    w : array, shape (n,)
        Array of window samples.

    Examples
    --------
    >>> from axopy.features.util import inverted_t_window
    >>> inverted_t_window(8)
    array([ 0.5,  1. ,  1. ,  1. ,  1. ,  1. ,  0.5,  0.5])
    """
    w = np.ones(n)
    w[:int(np.ceil(p * n)) - 1] = a
    w[int(np.floor((1-p) * n)):] = a

    return w


def trapezoidal_window(n, p=0.25):
    """Generate a symmetric trapezoidal window.

    The middle portion of the window is unity, while the onset and offset are
    linearly ramped up to 1 and down to 0, respectively.

    .. math::
       w_i =
       \\begin{cases}
           1, & pn \\leq i \\leq (1-p)n \\\\
           \\frac{i}{pn}, & i < pn \\\\
           \\frac{i - n}{pn}, & i > (1-p)n
       \\end{cases}

    Parameters
    ----------
    n : int
        Number of window samples to generate.
    p : float, optional
        Proportion of the window to consider as onset and offset. Should be
        less than 0.5.

    Returns
    -------
    w : array, shape (n,)
        Array of window samples.

    Examples
    --------
    >>> from axopy.features.util import trapezoidal_window
    >>> trapezoidal_window(9, p=1/3.)
    array([ 0.33333333,  0.66666667,  1.        ,  1.        ,  1.        ,
            1.        ,  0.66666667,  0.33333333,  0.        ])
    """
    w = np.ones(n)
    r1 = np.arange(0, int(np.ceil(p * n)) - 1)
    r2 = np.arange(int(np.floor((1-p) * n)), n)
    w[r1] = (1/p) * (r1 + 1) / n
    w[r2] = (1/p) * (n - (r2 + 1)) / n

    return w


def levinson(r, order=None, allow_singularity=False):
    """Levinson-Durbin recursion.

    Find the coefficients of an autoregressive linear process using the
    Levinson-Durbin recursion.

    Parameters
    ----------
    r : 1D array or list
        Autocorrelation sequence (first element is the zero-lag
        autocorrelation).
    order : int
        The order (p) of the auto-regressive model.
    allow_singularity : bool, optional
        Whether to allow singular matrices.

    Returns
    -------
    A : array, shape = (order,)
        The AR coefficients :math:`A=(a_1...a_p)`.
    """
    T0 = np.real(r[0])
    T = r[1:]
    M = len(T)

    if order is None:
        M = len(T)
    else:
        if M <= order:
            raise ValueError("Order must be less than size of the input data.")
        M = order

    realdata = np.isrealobj(r)
    if realdata is True:
        A = np.zeros(M, dtype=float)
        ref = np.zeros(M, dtype=float)
    else:
        A = np.zeros(M, dtype=complex)
        ref = np.zeros(M, dtype=complex)

    P = T0

    for k in range(0, M):
        save = T[k]
        if k == 0:
            temp = -save / P
        else:
            for j in range(0, k):
                save = save + A[j] * T[k-j-1]
            temp = -save / P
        if realdata:
            P = P * (1. - temp**2.)
        else:
            P = P * (1. - (temp.real**2+temp.imag**2))
        if P <= 0 and allow_singularity == False:
            raise ValueError("Singular matrix provided while "
                             "allow_singularity parameter was set to False.")
        A[k] = temp
        ref[k] = temp
        if k == 0:
            continue

        khalf = int((k+1)/2)
        if realdata is True:
            for j in range(0, khalf):
                kj = k-j-1
                save = A[j]
                A[j] = save + temp * A[kj]
                if j != kj:
                    A[kj] += temp*save
        else:
            for j in range(0, khalf):
                kj = k-j-1
                save = A[j]
                A[j] = save + temp * A[kj].conjugate()
                if j != kj:
                    A[kj] = A[kj] + temp * save.conjugate()

    return A


def nextpow2(n):
    """Returns the smaller power of 2 greater than or equal to n."""
    return 2**(np.ceil(np.log2(n))).astype(np.int)
