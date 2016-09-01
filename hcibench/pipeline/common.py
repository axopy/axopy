"""
Common processing tasks.
"""

import numpy as np
from scipy import signal

from .base import PipelineBlock


class Windower(PipelineBlock):
    """Windows incoming data to specific length.

    Takes new input data and combines with past data to maintain a sliding
    window with optional overlap.

    Input data is assumed to act like a numpy array with shape (num_channels,
    num_samples).

    Parameters
    ----------
    length : int
        Total number of samples to output on each iteration. This must be at
        least as large as the number of samples input to the windower on each
        iteration.
    """

    def __init__(self, length):
        super(Windower, self).__init__()
        self.length = length

        self.clear()

    def clear(self):
        self._out = None

    def process(self, data):
        if self._out is None:
            self._preallocate(data.shape[0])

        n = data.shape[1]
        if n == self.length:
            self._out = data
        else:
            self._out[:, :self.length-n] = self._out[:, -(self.length-n):]
            self._out[:, -n:] = data

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

    This block isn't strictly necessary, since you could just apply multiple
    feature blocks in parallel and the result of each will be passed to the
    next block. However, the block following feature computation typically
    expects the input to be a single array (or row) per data sample.

    Parameters
    ----------
    features : list
        List of (name, feature) tuples (i.e. implementing a ``compute``
        method).

    Attributes
    ----------
    named_features : dict
        Dictionary of features accessed by name.
    feature_indices : dict
        Dictionary of (start, stop) tuples indicating the bounds of each
        feature, accessed by name. Will be empty until after data is first
        passed through.
    """

    def __init__(self, features):
        super(FeatureExtractor, self).__init__()
        self.features = features

        self.feature_indices = {}
        self._output = None

    @property
    def named_features(self):
        return dict(self.features)

    def clear(self):
        """Clears the output array.

        This should be called if the input is going to change form in some
        way (i.e. the shape of the input array changes).
        """
        self.feature_indices = {}
        self._output = None

    def process(self, data):
        """Run data through the list of features and concatenates the results.

        The first pass (after a ``clear`` call) will be a little slow since the
        extractor needs to allocate the output array.

        Parameters
        ----------
        data : array, shape (n_channels, n_samples)
            Input data. Must be appropriate for all features.

        Returns
        -------
        out : array, shape (n_features,)
        """
        allocating = (self._output is None)
        ind = 0
        for i, (name, feature) in enumerate(self.features):
            if allocating:
                x = feature.compute(data)
                self.feature_indices[name] = (ind, ind+x.size)
                ind += x.size

                if self._output is None:
                    self._output = x
                else:
                    self._output = np.hstack([self._output, x])
            else:
                self._output[self.feature_indices[name][0]:
                             self.feature_indices[name][1]] = \
                    feature.compute(data)

        return self._output


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
