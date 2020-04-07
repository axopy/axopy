"""Common processing tasks implemented as Blocks."""

import warnings
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
    n_channels : int, optional
        Number of channels.
    channel_names : list, optional
        List of strings with channel names. By default, channel names are
        assigned numbers in increasing order using 0-based indexing.
    hooks : list, optional, default=None
        List of callables (callbacks) to run when after the block's `process`
        method is called.

    Attributes
    ----------
    named_features : dict
        Dictionary of features accessed by name.
    feature_indices : dict
        Dictionary of tuples indicating the indices of each feature, accessed
        by name. If none of ``n_channels`` or ``channel_names`` is provided,
        it will be empty until after data is first passed through.
    channel_indices : dict
        Dictionary of tuples indicating the indices of each feature, accessed
        by name. If none of ``n_channels`` or ``channel_names`` is provided,
        it will be empty until after data is first passed through.
    """

    def __init__(self, features, n_channels=None, channel_names=None,
                 hooks=None):
        super(FeatureExtractor, self).__init__(hooks=hooks)
        self.features = features
        self.n_channels, self.channel_names = self._check_channels(
            n_channels, channel_names)

        self.feature_indices, self.channel_indices = self._make_indices()
        self._output = None

    @property
    def named_features(self):
        return dict(self.features)

    @property
    def n_features_total(self):
        fpc = [feature.features_per_channel for (_, feature) in self.features]
        return np.array(fpc).sum() * self.n_channels

    def clear(self):
        """Clears the output array.

        This should be called if the input is going to change form in some
        way (i.e. the shape of the input array changes).
        """
        self.feature_indices = {}
        self.channel_indices = {}
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
        if (self._output is None):
            n_channels = data.shape[0]
            self.n_channels, self.channel_names = self._check_channels(
                n_channels=n_channels)
            self.feature_indices, self.channel_indices = self._make_indices()
            self._output = np.zeros((self.n_features_total,))

        for i, (name, feature) in enumerate(self.features):
            self._output[list(self.feature_indices[name])] = \
                feature.compute(data)

        return self._output

    def _check_channels(self, n_channels=None, channel_names=None):
        """Performs checks for arguments ``n_channels`` and ``channel_names``.

        Parameters
        ----------
        n_channels : int
            Number of channels.

        channel_names : list
            Channel names.

        Returns
        -------
        n_channels : int
            Number of channels.

        channel_names : list
            Channel names.
        """
        if channel_names is None:
            if n_channels is None:
                pass
            else:
                channel_names = [str(c) for c in range(n_channels)]
        else:
            if n_channels is None:
                n_channels = len(channel_names)
            else:
                if n_channels != len(channel_names):
                    raise ValueError("Inconsistent number of channels and " +
                                     "channel names.")

        return (n_channels, channel_names)

    def _make_indices(self):
        if self.n_channels is None and self.channel_names is None:
            feature_indices = {}
            channel_indices = {}
        else:
            feature_indices = {}
            ind = 0
            for (name, feature) in self.features:
                feature_indices[name] = tuple(range(
                    ind, ind + self.n_channels * feature.features_per_channel))
                ind += self.n_channels * feature.features_per_channel

            channel_indices = {}

            for c_idx, channel in enumerate(self.channel_names):
                channel_indices[channel] = tuple(range(
                    c_idx, self.n_features_total, self.n_channels))

        return (feature_indices, channel_indices)


class Selector(Block):
    """Selects a subset of features according to some property.

    This block is intended to be used only after a ``FeatureExtractor`` block.

    Parameters
    ----------
    items : list
        List of strings specifying the items to be selected.

    item_indices : dict
        Dictionary of tuples indicating the indices of each item, accessed
        by name.
    """

    def __init__(self, items, item_indices):
        super(Selector, self).__init__()
        self.items = items
        self.item_indices = item_indices

        self._initialize()

    def _initialize(self):
        """Compute the indices corresponding to the specified items. """
        self._indices = []
        for item in self.items:
            self._indices.extend(self.item_indices[item])
        self._indices.sort()

    def process(self, data):
        """Selects the specified items. """
        return data[self._indices]


class ChannelSelector(Selector):
    """Selects features from specified channels.

    This block is intended to be used only after a ``FeatureExtractor`` block,
    using the ``channel_indices`` attribute.

    Parameters
    ----------
    channels : list
        List of strings specifying the channels to be selected.

    channel_indices : dict
        Dictionary of tuples indicating the indices of each channel, accessed
        by name.
    """

    def __init__(self, channels, channel_indices):
        super(ChannelSelector, self).__init__(channels, channel_indices)


class FeatureSelector(Selector):
    """Selects specified features.

    This block is intended to be used only after a ``FeatureExtractor`` block,
    using the ``feature_indices`` attribute.

    Parameters
    ----------
    features : list
        List of strings specifying the features to be selected.

    feature_indices : dict
        Dictionary of tuples indicating the indices of each feature, accessed
        by name.
    """

    def __init__(self, features, feature_indices):
        super(FeatureSelector, self).__init__(features, feature_indices)


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
    return_proba : boolean, optional (default: False)
        If True, use the estimator's ``predict_proba`` method instead of
        ``predict`` to return probability estimates.
    return_log_proba : boolean, optional (default: False)
        If True, use the estimator's ``predict_log_proba`` method instead of
        ``predict`` to return probability estimates.
        """

    def __init__(self, estimator, return_proba=False, return_log_proba=False):
        super(Estimator, self).__init__()
        self.estimator = estimator
        self.return_proba = return_proba
        self.return_log_proba = return_log_proba
        self._check_estimator()

    def process(self, data):
        """Calls the estimator's ``predict`` or ``predict_proba`` method and
        returns the result."""
        if self.return_proba:
            return self.estimator.predict_proba(data)
        elif self.return_log_proba:
            return self.estimator.predict_log_proba(data)
        else:
            return self.estimator.predict(data)

    def _check_estimator(self):
        """Check estimator attributes when either ``return_proba`` or
        ``return_log_proba`` are set to ``True``.

        If both arguments are True use ``predict_proba`` and issue a warning.
        """
        if not hasattr(self.estimator, 'predict_proba') and self.return_proba:
            raise ValueError("Estimator {} does not implement a "
                             "predict_proba method".format(self.estimator))
        if not hasattr(self.estimator, 'predict_log_proba') and \
                self.return_log_proba:
            raise ValueError("Estimator {} does not implement a "
                             "predict_log_proba method".format(self.estimator))

        if self.return_proba and self.return_log_proba:
            warnings.warn("Both predict_proba and predict_log_proba were set "
                          "to True for estimator {}. The process method will "
                          "default to predict_proba.".format(self.estimator))
            self.return_log_proba = False


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
        implementing ``fit``, ``transform`` and ``inverse_transform`` methods).
    inverse : boolean, optional (default: False)
        If True, call ``inverse_transform`` instead of ``transform``.
    """

    def __init__(self, transformer, inverse=False, hooks=None):
        super(Transformer, self).__init__(hooks=None)
        self.transformer = transformer
        self.inverse = inverse

    def process(self, data):
        """Calls the transformer's ``transform`` or ``inverse_transform``
        method and returns the result.
        """
        if self.inverse:
            return self.transformer.inverse_transform(data)
        else:
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


class MinMaxScaler(Block):
    """Scales data between specified minimum and maximum values.

    Parameters
    ----------
    min_ : array or list, shape (n_channels,)
        Minimum values.
    max_ : array or list, shape (n_channels,)
        Maximum values.
    """

    def __init__(self, min_, max_):
        super(MinMaxScaler, self).__init__()
        self.min = np.asarray(min_)
        self.max = np.asarray(max_)

        if min_.shape != max_.shape:
            raise ValueError("Scaling arrays must have the same shape.")

        if min_.ndim != 1 or max_.ndim != 1:
            raise ValueError("Scaling arrays must be 1-dimensional.")

    def process(self, data):
        """Scales the data.

        Parameters
        ----------
        data : array, shape (n_channels,) or (dim_1, dim_2, ..., n_channels)
            Input data.
        """
        if data.shape[-1] != self.min.shape[0]:
            raise ValueError("The last dimension of the input data must match "
                             "that of the scalling arrays.")

        data_sc = (data-self.min) / (self.max-self.min)
        return data_sc
