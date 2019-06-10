"""Functions to compute sample entropy.

Source: https://en.wikipedia.org/wiki/Sample_entropy

License: Creative Commons Attribution-ShareAlike 3.0 Unported License

THE WORK (AS DEFINED BELOW) IS PROVIDED UNDER THE TERMS OF THIS CREATIVE COMMONS
PUBLIC LICENSE ("CCPL" OR "LICENSE"). THE WORK IS PROTECTED BY COPYRIGHT AND/OR
OTHER APPLICABLE LAW. ANY USE OF THE WORK OTHER THAN AS AUTHORIZED UNDER THIS
LICENSE OR COPYRIGHT LAW IS PROHIBITED.

BY EXERCISING ANY RIGHTS TO THE WORK PROVIDED HERE, YOU ACCEPT AND AGREE TO BE
BOUND BY THE TERMS OF THIS LICENSE. TO THE EXTENT THIS LICENSE MAY BE CONSIDERED
TO BE A CONTRACT, THE LICENSOR GRANTS YOU THE RIGHTS CONTAINED HERE IN
CONSIDERATION OF YOUR ACCEPTANCE OF SUCH TERMS AND CONDITIONS.
"""

import numpy as np


def sample_entropy_1d(x, m, r, delta):
    """Core algorithm for computing sample entropy of 1D time-series data."""
    x = x[::delta]
    return -np.log(_phi(x, m + 1, r) / _phi(x, m, r))


def _maxdist(x_i, x_j):
    """Computes the Chebyshev distance between two points in the
    embedded space. Required for sample entropy estimation.
    """
    result = np.max([np.abs(ua - va) for ua, va in zip(x_i, x_j)])
    return result


def _phi(x, m, r):
    """Computes the number of template vector pairs having a smaller distance
    than tolerance. Required for sample entropy estimation.
    """
    N = len(x)
    x_ = [[x[j] for j in range(i, i + m - 1 + 1)] for i in range(
        N - m + 1)]
    C = [len([1 for j in range(len(x_)) if i != j and
              _maxdist(x_[i], x_[j]) <= r]) for i in range(len(x_))]
    return np.sum(C)
