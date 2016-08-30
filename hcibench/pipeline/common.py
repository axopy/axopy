"""
Common processing tasks.
"""

import numpy as np
from scipy import signal

from .base import PipelineBlock


class Windower(PipelineBlock):
    """Windows incoming data to specific length and overlap.

    Takes new input data and combines with past data to maintain a sliding
    window with overlap. It is assumed that the input to this block has length
    (length-overlap).

    Input data is assumed to act like a numpy array with shape (num_channels,
    num_samples).

    Parameters
    ----------
    length : int
        Total number of samples to output on each iteration.
    overlap : int, optional
        Number of samples from previous input to keep in the current window.
        Default is 0, which means there is no overlap between updates.
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
            self._preallocate(data.shape[0])

        if self.overlap == 0:
            return data

        self._out[:, :self.overlap] = self._out[:, -self.overlap:]
        self._out[:, self.overlap:] = data

        return self._out.copy()

    def _preallocate(self, num_channels):
        self._out = np.zeros((num_channels, self.length))


class Filter(PipelineBlock):
    """Filters incoming data with a time domain filter.

    This filter implementation takes filter coefficients that are designed
    by the user -- it merely applies the filter to the input, remembering the
    final inputs/outputs from the previous update and using them as initial
    conditions for the current update.

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
        Default is 0, meaning the final inputs/outputs of the previous update
        are used.
    """

    def __init__(self, b, a=1, overlap=0):
        super(Filter, self).__init__()
        self.b = b
        self.a = a
        self.overlap = overlap

        self.clear()

    def clear(self):
        """Clears the filter initial conditions.

        Clearing the initial conditions is important when starting a new
        recording.
        """
        self.x_prev = None
        self.y_prev = None

    def process(self, data):
        """Applies the filter to the input.

        Parameters
        ----------
        data : ndarray, shape (n_channels, n_samples)
            Input signals.
        """
        if self.x_prev is None:
            # first pass has no initial conditions
            out = signal.lfilter(
                self.b, self.a, data, axis=-1)
        else:
            # subsequent passes get ICs from previous input/output
            num_ch = data.shape[0]
            K = max(len(self.a)-1, len(self.b)-1)
            self.zi = np.zeros((num_ch, K))
            # unfortunately we have to get zi channel by channel
            for c in range(data.shape[0]):
                self.zi[c, :] = signal.lfiltic(
                    self.b,
                    self.a,
                    self.y_prev[c, -(self.overlap+1)::-1],
                    self.x_prev[c, -(self.overlap+1)::-1])

            out, zf = signal.lfilter(
                self.b, self.a, data, axis=-1, zi=self.zi)

        self.x_prev = data
        self.y_prev = out
        return out


class FeatureExtractor(PipelineBlock):
    """Computes multiple features from the input, concatenating the results.

    Each feature should be able to take in the same data and output a 1D array,
    so overall output of the FeatureExtractor can be a single 1D array.

    Parameters
    ----------
    features : list
        List of (name, feature) tuples (i.e. implementing a ``compute``
        method).

    Attributes
    ----------
    named_features : dict
        Dictionary of features accessed by name.
    """

    def __init__(self, features):
        super(FeatureExtractor, self).__init__()
        self.features = features

        self._output = None

    @property
    def named_features(self):
        return dict(self.features)

    def clear(self):
        """Clears the output array.

        This should be called if the input is going to change form in some
        way (i.e. the shape of the input array changes).
        """
        self._output = None

    def process(self, data):
        """Run data through the list of features.

        Parameters
        ----------
        data : array
            Input data. Must be appropriate for all features.
        """
        pass


class Estimator(PipelineBlock):
    """A pipeline block wrapper around scikit-learn's idea of an estimator.

    An estimator is an object that can be trained with some data (``fit``) and,
    once trained, can output predictions from novel inputs. A common use-case
    for this block is to utilize a scikit-learn pipeline in the context of a
    hcibench pipeline.

    Parameters
    ----------
    estimator : object
        An object implementing the scikit-learn Estimator interface (i.e.
        implementing ``fit`` and ``predict`` methods).
    """

    def __init__(self, estimator):
        super(Estimator, self).__init__()
        self.estimator = estimator

    def process(self, data):
        """Calls the estimator's ``predict`` method and returns the result."""
        return self.estimator.predict(data)


class Transformer(PipelineBlock):
    """A pipeline block wrapper around scikit-learn's idea of a transformer.

    A transformer is trained with some data (``fit``) and, once trained, can
    output projections of the input data to some other space. A common example
    is projecting data in high-dimensional space to a lower-dimensional space
    using principal components analysis.

    Parameters
    ----------
    transformer : object
        An object implementing the scikit-learn Transformer interface (i.e.
        implementing ``fit`` and ``transform`` methods).
    """

    def __init__(self, transformer):
        super(Transformer, self).__init__()
        self.transformer = transformer

    def process(self, data):
        """Calls the transformer's ``transform`` method and returns the result.
        """
        return self.transformer.transform(data)
