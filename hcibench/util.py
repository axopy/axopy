"""
Utility functions.
"""

import numpy as np


def ensure_2d(array):
    """
    Makes sure the input array has at least 2 dimensions. Useful for handling
    arrays with shape=(n,).
    """
    if array.ndim == 1:
        array = np.atleast_2d(array)
    return array


def rolling_window(array, n):
    """
    Creates a rolling window from an array by adding an extra axis to
    efficiently compute statistics over. Use `axis=-1` to remove the extra
    axis.

    Parameters
    ----------
    array : ndarray
        The input array.
    n : int
        Window length.

    Returns
    -------
    window : ndarray
        The length-n windows of the input array.

    Examples
    --------
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
