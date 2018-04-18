"""Common processing tasks implemented as Blocks."""

import numpy as np
from scipy import signal

from axopy.pipeline import Pipeline, Block


class Passthrough(Pipeline):
    """Convenience block for passing input along to output.

    A passthrough pipeline block is useful when you want to process some data
    then provide both the processed output as well as the original input to
    another block downstream::

            -----------------------> x
           |
        x ---> [ subpipeline ] ----> y
    """

    def __init__(self, blocks, expand_output=True, name=None):
        super(Passthrough, self).__init__(blocks, name=name)
        self.expand_output = expand_output

    def process(self, data):
        out = super(Passthrough, self).process(data)
        if self.expand_output:
            ldata = [data]
            ldata.extend(out)
            return ldata
        else:
            return data, out


class Callable(Block):
    """A `Block` that does not require persistent attributes.

    Some `Block` implementations don't require attributes to update on
    successive calls to the `process` method, but instead are essentially a
    function that can be called repeatedly. This class is for conveniently
    creating such a block.

    If the function you want to use takes additional arguments, such as a
    keyword argument that

    Note: if you use an anonymous function as the `func` argument, (e.g.
    ``lambda x: 2*x``), it is recommended to explicitly give the block a
    meaningful name.

    Parameters
    ----------
    func : callable(x)
        Function that gets called when the block's `process` method is called.
        Should take a single input and return output which is compatible with
        whatever is connected to the block.
    func_args : list, optional
        List (or tuple) of additional arguments to pass to `func` when calling
        it for processing. If None (default), no arguments are used.
    func_kwargs : dict
        Keyword argument name/value pairs to pass to `func` when calling it for
        processing. If None (default), no keyword arguments are used.
    name : str, optional, default=None
        Name of the block. By default, the name of the `processor` function is
        used.
    hooks : list, optional, default=None
        List of callables (callbacks) to run when after the block's `process`
        method is called.
    """

    def __init__(self, func, func_args=None, func_kwargs=None, name=None,
                 hooks=None):
        if name is None:
            name = func.__name__
        super(Callable, self).__init__(name=name, hooks=hooks)
        self.func = func
        self.func_args = func_args if func_args is not None else []
        self.func_kwargs = func_kwargs if func_kwargs is not None else {}

    def process(self, data):
        return self.func(data, *self.func_args, **self.func_kwargs)


class Windower(Block):
    """Windows incoming data to a specific length.

    Takes new input data and combines with past data to maintain a sliding
    window with optional overlap. The window length is specified directly, so
    the overlap depends on the length of the input.

    The input length may change on each iteration, but the ``Windower`` must be
    cleared before the number of channels can change.

    Parameters
    ----------
    length : int
        Total number of samples to output on each iteration. This must be at
        least as large as the number of samples input to the windower on each
        iteration.

    See Also
    --------
    axopy.pipeline.common.Ensure2D: Ensure input to the windower is 2D.

    Examples
    --------
    Basic use of a windower:

    >>> import axopy.pipeline as pipeline
    >>> import numpy as np
    >>> win = pipeline.Windower(4)
    >>> win.process(np.array([[1, 2], [3, 4]]))
    array([[ 0.,  0.,  1.,  2.],
           [ 0.,  0.,  3.,  4.]])
    >>> win.process(np.array([[7, 8], [5, 6]]))
    array([[ 1.,  2.,  7.,  8.],
           [ 3.,  4.,  5.,  6.]])
    >>> win.clear()
    >>> win.process(np.array([[1, 2], [3, 4]]))
    array([[ 0.,  0.,  1.,  2.],
           [ 0.,  0.,  3.,  4.]])

    If your data is 1-dimensional (shape ``(n_samples,)``), use an
    :class:`Ensure2D` block in front of the :class:`Windower`:

    >>> win = pipeline.Windower(4)
    >>> p = pipeline.Pipeline([pipeline.Ensure2D(), win])
    >>> p.process(np.array([1, 2]))
    array([[ 0.,  0.,  1.,  2.]])
    """

    def __init__(self, length):
        super(Windower, self).__init__()
        self.length = length

        self.clear()

    def clear(self):
        """Clear the buffer containing previous input data.
        """
        self._out = None

    def process(self, data):
        """Add new data to the end of the window.

        Parameters
        ----------
        data : array, shape (n_channels, n_samples)
            Input data. ``n_samples`` must be less than or equal to the
            windower ``length``.

        Returns
        -------
        out : array, shape (n_channels, length)
            Output window with the input data at the end.
        """
        if data.ndim != 2:
            raise ValueError("data must be 2-dimensional.")

        n = data.shape[1]

        if n > self.length:
            raise ValueError("data must be shorter than window length.")

        if self._out is None:
            self._preallocate(data.shape[0])

        if data.shape[0] != self._out.shape[0]:
            raise ValueError("Number of channels cannot change without "
                             "calling clear first.")

        if n == self.length:
            self._out = data
        else:
            self._out[:, :self.length-n] = self._out[:, -(self.length-n):]
            self._out[:, -n:] = data

        return self._out.copy()

    def _preallocate(self, n_channels):
        self._out = np.zeros((n_channels, self.length))


class Centerer(Block):
    """Centers data by subtracting out its mean.

    .. math:: \\tilde{x} = x - \\sum_{i=0}^{N-1} x[i]
    """

    def process(self, data):
        """Center each row of the input.

        Parameters
        ----------
        data : array, shape (n_channels, n_samples)
            Input data.

        Returns
        -------
        out : array, shape (n_channels, n_samples)
            Input data that's been centered.
        """
        return data - np.mean(data)


class Filter(Block):
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

    See Also
    --------
    axopy.pipeline.common.Ensure2D: Ensure input to the filter is 2D.

    Examples
    --------
    Design a filter using scipy and use the coefficients:

    >>> import axopy.pipeline as pipeline
    >>> import numpy as np
    >>> from scipy.signal import butter
    >>> b, a = butter(4, 100/1000/2)
    >>> f = pipeline.Filter(b, a)
    >>> f.process(np.random.randn(1, 5)) # doctest: +ELLIPSIS
    array([...

    Use a filter in combination with a :class:`Windower`, making sure to
    account for overlapping data in consecutive filtering operations. Here,
    we'll use a window of length 5 and pass in 3 samples at a time, so there
    will be an overlap of 2 samples. The overlapping samples in each output
    will agree:

    >>> w = pipeline.Windower(5)
    >>> f = pipeline.Filter(b, a, overlap=2)
    >>> p = pipeline.Pipeline([w, f])
    >>> out1 = p.process(np.random.randn(1, 3))
    >>> out2 = p.process(np.random.randn(1, 3))
    >>> out1[:, -2:] == out2[:, :2]
    array([[ True,  True]], dtype=bool)

    """

    def __init__(self, b, a=1, overlap=0):
        super(Filter, self).__init__()
        self.b = b
        self.a = np.atleast_1d(a)
        self.overlap = overlap

        self.clear()

    def clear(self):
        """Clears the filter initial conditions.

        Clearing the initial conditions is important when starting a new
        recording if ``overlap`` is nonzero.
        """
        self._x_prev = None
        self._y_prev = None

    def process(self, data):
        """Applies the filter to the input.

        Parameters
        ----------
        data : ndarray, shape (n_channels, n_samples)
            Input signals.
        """
        if data.ndim != 2:
            raise ValueError("data must be 2-dimensional.")

        if self._x_prev is None:
            # first pass has no initial conditions
            out = signal.lfilter(self.b, self.a, data, axis=-1)
        else:
            # subsequent passes get ICs from previous input/output
            num_ch = data.shape[0]
            K = max(len(self.a)-1, len(self.b)-1)
            self._zi = np.zeros((num_ch, K))

            # unfortunately we have to get zi channel by channel
            for c in range(data.shape[0]):
                self._zi[c, :] = signal.lfiltic(
                    self.b,
                    self.a,
                    self._y_prev[c, -(self.overlap+1)::-1],
                    self._x_prev[c, -(self.overlap+1)::-1])

            out, zf = signal.lfilter(self.b, self.a, data, axis=-1,
                                     zi=self._zi)

        self._x_prev = data
        self._y_prev = out

        return out


class FeatureExtractor(Block):
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

    def __init__(self, features, hooks=None):
        super(FeatureExtractor, self).__init__(hooks=hooks)
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


class Estimator(Block):
    """A pipeline block wrapper around scikit-learn's idea of an estimator.

    An estimator is an object that can be trained with some data (``fit``) and,
    once trained, can output predictions from novel inputs. A common use-case
    for this block is to utilize a scikit-learn pipeline in the context of a
    axopy pipeline.

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


class Transformer(Block):
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

    def __init__(self, transformer, hooks=None):
        super(Transformer, self).__init__(hooks=None)
        self.transformer = transformer

    def process(self, data):
        """Calls the transformer's ``transform`` method and returns the result.
        """
        return self.transformer.transform(data)


class Ensure2D(Block):
    """Transforms an array to ensure it has 2 dimensions.

    Input with shape ``(n,)`` can be made to have shape ``(n, 1)`` or
    ``(1, n)``.

    Parameters
    ----------
    orientation : {'row', 'col'}, optional
        Orientation of the output. If 'row', the output will have shape
        ``(1, n)``, meaning the output is a row vector. This is the default
        behavior, useful when the data is something like samples of a 1-channel
        signal.  If 'col', the output will have shape ``(n, 1)``, meaning the
        output is a column vector.

    Examples
    --------
    Output row data:

    >>> import numpy as np
    >>> import axopy.pipeline as pipeline
    >>> block = pipeline.Ensure2D()
    >>> block.process(np.array([1, 2, 3]))
    array([[1, 2, 3]])

    Output column data:

    >>> block = pipeline.Ensure2D(orientation='col')
    >>> block.process(np.array([1, 2, 3]))
    array([[1],
           [2],
           [3]])
    """

    def __init__(self, orientation='row'):
        super(Ensure2D, self).__init__()
        self.orientation = orientation

        if orientation not in ['row', 'col']:
            raise ValueError("orientation must be either 'row' or 'col'")

    def process(self, data):
        """Make sure data is 2-dimensional.

        If the input already has two dimensions, it is unaffected.

        Parameters
        ----------
        data : array, shape (n,)
            Input data.

        Returns
        -------
        out : array, shape (1, n) or (n, 1)
            Output data, with shape specified by ``orientation``.
        """
        data = np.atleast_2d(data)

        if self.orientation == 'row':
            return data
        else:
            return data.T
