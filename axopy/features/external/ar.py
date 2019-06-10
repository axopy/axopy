"""Functions to compute auto-regressive coefficients.

Source: https://github.com/cokelaer/spectrum

Copyright (c) 2011-2017, Thomas Cokelaer
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of spectrum nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import numpy as np
from scipy.fftpack import fft, ifft
from axopy.features.util import nextpow2


def autocorrelation(x, axis):
    """Compute autocorrelation matrix using FFT.

    Parameters
    ----------
    x : ndarray
        Input data. Use the ``axis`` argument to specify the "time axis".
    axis : int, optional
        The time axis.

    Returns
    -------
    R : array, shape (n_channels, n_channels)
        Autocorrelation matrix.
    """
    x = np.asarray(x)
    m = x.shape[axis]
    X = fft(x, n=nextpow2(m), axis=axis)
    R = np.real(ifft(np.abs(X)**2, axis=axis))  # Auto-correlation matrix
    R = R / (m-1)

    return R


def levinson(r, order, allow_singularity):
    """Levinson-Durbin recursion. Required for AR estimation.

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

    if M <= order:
        raise ValueError("Order must be less than size of the input "
                         "data.")
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
                             "allow_singularity parameter was set to "
                             "False.")
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
