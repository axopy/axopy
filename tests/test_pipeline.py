import pytest
import numpy as np
from scipy import signal

from numpy.testing import (assert_array_equal, assert_array_almost_equal,
                           assert_equal)

import axopy.pipeline as pipeline
from axopy.features.classes import _FeatureBase

np.random.seed(12345)

rand_data_1d = np.random.rand(100)
rand_data_2d1 = np.random.rand(1, 100)
rand_data_2d = np.random.rand(5, 100)

b, a = signal.butter(2, (10/1000., 450/1000.), btype='bandpass')


#
# axopy.pipeline.core tests
#

data = 4.3


def _f(x):
    return 2 * x + 1


def _g(x):
    return (x + 3) / (3 - x)


def _twoin(x, y):
    return (4 * x) + y + 3


def _threein(x, y, z):
    return (x * y) + z


class _FBlock(pipeline.Block):

    def process(self, data):
        return _f(data)


class _GBlock(pipeline.Block):

    def process(self, data):
        return _g(data)


class _TwoIn(pipeline.Block):

    def process(self, data):
        a, b = data
        return _twoin(a, b)


class _ThreeIn(pipeline.Block):

    def process(self, data):
        a, b, c = data
        return _threein(a, b, c)


class _Stateful(pipeline.Block):

    def __init__(self, initial):
        super(_Stateful, self).__init__()
        self.initial = initial
        self.clear()

    def clear(self):
        self.data = self.initial

    def process(self, data):
        self.data = _f(data)
        return self.data


class _NamedBlock(pipeline.Block):

    def __init__(self, name=None):
        super(_NamedBlock, self).__init__(name=name)


class _HookEnabledBlock(pipeline.Block):

    def __init__(self, hooks=None):
        super(_HookEnabledBlock, self).__init__(hooks=hooks)

    def process(self, data):
        return _f(data)


def test_series():
    """
    Simple series test:

        -- a - b --
    """
    a = _FBlock()
    b = _GBlock()
    p = pipeline.Pipeline([a, b])
    result = p(data)

    assert result == _g(_f(data))


def test_parallel():
    """
    Simple parallel structure:

          .- a -.
          |     |
        --+     +==
          |     |
          '- b -'
    """
    a = _FBlock()
    b = _GBlock()
    p = pipeline.Pipeline((a, b))
    result = p.process(data)

    assert result == [_f(data), _g(data)]


def test_parallel_series():
    """
    Simple parallel to series structure:

          .- a -.
          |     |
        --+     += c --
          |     |
          '- b -'
    """
    a = _FBlock()
    b = _GBlock()
    c = _TwoIn()
    p = pipeline.Pipeline([(a, b), c])
    result = p.process(data)

    assert result == _twoin(_f(data), _g(data))


def test_composite():
    """
    Composite pipeline (pipeline within a pipeline):

        m:
            -- a - b --
        p:
              .- m -.
              |     |
            --+     += d --
              |     |
              '- c -'
    """
    a = _FBlock()
    b = _GBlock()
    m = pipeline.Pipeline([a, b])
    c = _FBlock()
    d = _TwoIn()
    p = pipeline.Pipeline([(m, c), d])
    result = p.process(data)

    assert result == _twoin(_g(_f(data)), _f(data))


def test_passthrough():
    """
    Pass-through pipeline test

        m:
              .--------.
              |        |
              +- b -.  |
              |     |  |
            --+     +==+==
              |     |
              '- c -'
        p:
            -- a - m = d --
    """
    b = _FBlock()
    c = _GBlock()
    m = pipeline.Passthrough((b, c))
    a = _FBlock()
    d = _ThreeIn()
    p = pipeline.Pipeline([a, m, d])
    result = p.process(data)

    ares = _f(data)
    assert result == _threein(ares, _f(ares), _g(ares))


def test_passthrough_noexpand():
    # test passthrough block without expanding output
    a = _FBlock()
    b = _GBlock()
    c = pipeline.Passthrough((a, b), expand_output=False)
    assert c.process(data) == (data, [_f(data), _g(data)])


def test_clear():
    # clearing a stateful block.
    init = 4
    b = _Stateful(init)
    p = pipeline.Pipeline([b])
    p.process(data)

    assert b.data == _f(data)
    b.clear()
    assert b.data == init


def test_clear_pass():
    # make sure clear passes
    a = pipeline.Block()
    a.clear()

    f = _FBlock()
    f.clear()


def test_clear_pipeline():
    init = 4
    b = _Stateful(init)
    p = pipeline.Pipeline([b])
    p.process(data)

    p.clear()
    assert b.data == init


def test_parallel_clear():
    # see issue #70
    p = pipeline.Pipeline([
        (_FBlock(), _GBlock()),
        _TwoIn()
    ])
    out = p.process(data)
    p.clear()


def test_block_repr():
    b = pipeline.Block()
    assert repr(b) == 'axopy.pipeline.core.Block()'


def test_process_unimplemented():
    # unimplemented process method should raise error
    a = pipeline.Block()
    with pytest.raises(NotImplementedError):
        a.process(0)

    class BadBlock(pipeline.Block):
        pass

    a = BadBlock()
    with pytest.raises(NotImplementedError):
        a.process(0)


def test_named_block():
    # make sure block naming works.
    b = _NamedBlock()
    assert b.name == '_NamedBlock'

    b2 = _NamedBlock('blockname')
    assert b2.name == 'blockname'


def test_hooks():
    # test hooks for intermediate blocks.
    def hook1(out):
        assert out == _f(data)

    def hook2(out):
        assert out == _f(data)

    # first test just one hook
    a = _HookEnabledBlock(hooks=[hook1])
    b = _GBlock()

    p = pipeline.Pipeline([a, b])
    result = p.process(data)

    assert result == _g(_f(data))

    # test multiple hooks
    a = _HookEnabledBlock(hooks=[hook1, hook2])
    p = pipeline.Pipeline([a, b])

    result = p.process(data)

    assert result == _g(_f(data))


def test_block_access():
    # test access to blocks in a pipeline using `named_blocks`.
    a = _NamedBlock(name='a')
    b = _NamedBlock(name='b')

    p = pipeline.Pipeline([a, b])

    assert p.named_blocks['a'] is a
    assert p.named_blocks['b'] is b
    assert p.named_blocks['a'] is not b
    assert p.named_blocks['b'] is not a


def test_named_subpipeline():
    # any block that wraps a sub-pipeline is accessible through
    # ``named_blocks``, but the sub-pipeline blocks are not
    a = _NamedBlock(name='sub_a')
    b = _NamedBlock(name='sub_b')
    c = _NamedBlock(name='c')

    passthrough = pipeline.Passthrough([a, b], name='passthrough')
    p = pipeline.Pipeline([passthrough, c])

    names = list(p.named_blocks)
    assert 'passthrough' in names
    assert 'c' in names
    assert 'sub_a' not in names

    assert 'sub_b' in p.named_blocks['passthrough'].named_blocks


def test_callable_block():
    # test block creation from function
    a = _FBlock()
    b = pipeline.Callable(_g)
    p = pipeline.Pipeline([a, b])
    result = p.process(data)
    assert result == _g(_f(data))

    # lambdas work too
    a = pipeline.Callable(lambda x: x + 2)
    assert a.process(3) == 5

    # check that naming works -- use name of function, not the class
    a = pipeline.Callable(_g)
    assert a.name == '_g'


def test_callable_block_with_args():
    # pass additional args/kwargs to the function
    def func(data, param, kwarg=None):
        return param, kwarg

    a = pipeline.Callable(func, func_args=(42,), func_kwargs={'kwarg': 10})
    assert a.process(3) == (42, 10)


#
# axopy.pipeline.common tests
#

class _NthSampleFeature(_FeatureBase):
    def __init__(self, ind, channel=None):
        super().__init__(features_per_channel=1)
        self.ind = ind
        self.channel = channel

    def compute(self, data):
        if self.channel is None:
            return data[:, self.ind]
        else:
            return data[self.channel, self.ind]


class _RandomMultipleFeature(_FeatureBase):
    def __init__(self, features_per_channel):
        super().__init__(features_per_channel=features_per_channel)
        self.features_per_channel = features_per_channel

    def compute(self, data):
        return np.random.randn(self.features_per_channel * data.shape[0],)


def _window_generator(data, length):
    for i in range(0, data.shape[-1], length):
        yield data[:, i:i+length]


def test_windower_no_overlap():
    # make sure windower handles data the same length as the window
    data = rand_data_2d
    windower = pipeline.Windower(10)

    for samp in _window_generator(data, 10):
        win = windower.process(samp)

    assert_array_equal(win, data[:, -10:])


def test_windower_overlap():
    # make sure window overlap works correctly
    data = rand_data_2d
    windower = pipeline.Windower(13)

    for samp in _window_generator(data, 10):
        win = windower.process(samp)

    assert_array_equal(win, data[:, -13:])


def test_windower_1d():
    # make sure a 1D array raises an error
    data = np.array([1, 2, 3, 4])
    windower = pipeline.Windower(10)

    with pytest.raises(ValueError):
        windower.process(data)


def test_windower_short():
    # make sure an exception is raised if the window length is too short
    data = rand_data_2d
    windower = pipeline.Windower(data.shape[1]-1)

    with pytest.raises(ValueError):
        windower.process(data)


def test_windower_clear():
    # make sure clearing the windower allows for changing number of channels
    data = rand_data_2d
    windower = pipeline.Windower(data.shape[1]+1)
    windower.process(data)

    with pytest.raises(ValueError):
        windower.process(rand_data_2d1)

    windower.clear()

    windower.process(rand_data_2d1)


def test_centerer():
    data = np.array([-1, 1, -1, 1])
    centerer = pipeline.Centerer()
    assert_array_equal(centerer.process(data), data)

    data = rand_data_2d
    assert data.shape == centerer.process(data).shape


def test_filter_overlap():
    # make sure output is continuous when filtering overlapped data
    data = rand_data_2d
    win_length = 10
    overlap = 5
    block = pipeline.Filter(b, a, overlap=overlap)

    data1 = data[:, 0:win_length]
    data2 = data[:, win_length-overlap:win_length-overlap+win_length]
    out1 = block.process(data1)
    out2 = block.process(data2)

    assert_array_almost_equal(out1[:, -overlap:], out2[:, :overlap])


def test_filter_1d():
    # make sure a 1D array raises an error
    data = np.array([1, 2, 3, 4])
    block = pipeline.Filter(b, a)

    with pytest.raises(ValueError):
        block.process(data)


def test_fir_filter():
    # use default parameter for a
    data = rand_data_2d
    block = pipeline.Filter(b)
    block.process(data)
    block.process(data)


def test_fextractor_simple():
    f0 = _NthSampleFeature(0)
    ex = pipeline.FeatureExtractor([('0', f0),
                                    ('1', _NthSampleFeature(1))])
    data = np.array([[0, 1, 2, 3, 4],
                     [5, 6, 7, 8, 9]])

    assert_array_equal(np.array([0, 5, 1, 6]), ex.process(data))

    assert ex.feature_indices['0'] == (0, 1)
    assert ex.feature_indices['1'] == (2, 3)

    assert ex.channel_indices['0'] == (0, 2)
    assert ex.channel_indices['1'] == (1, 3)

    assert ex.named_features['0'] is f0


def test_fextractor_clear():
    ex = pipeline.FeatureExtractor([('0', _NthSampleFeature(0)),
                                    ('1', _NthSampleFeature(2))])
    data_2ch = np.array([[0, 1, 2, 3, 4],
                         [5, 6, 7, 8, 9]])
    data_1ch = np.array([[0, 1, 2, 3, 4]])

    assert_array_equal(np.array([0, 5, 2, 7]), ex.process(data_2ch))
    ex.clear()
    assert_array_equal(np.array([0, 2]), ex.process(data_1ch))


def test_fextractor_indices_with_names():
    ex = pipeline.FeatureExtractor(
        [('rand', _RandomMultipleFeature(features_per_channel=2)),
         ('0', _NthSampleFeature(0))],
        channel_names=['channel_1', 'channel_2'])
    assert ex.channel_indices == {
        'channel_1': (0, 2, 4),
        'channel_2': (1, 3, 5)}
    assert ex.feature_indices == {'rand': (0, 1, 2, 3), '0': (4, 5)}


def test_fextractor_indices_with_channel_number():
    ex = pipeline.FeatureExtractor(
        [('rand', _RandomMultipleFeature(features_per_channel=2)),
         ('0', _NthSampleFeature(0))],
        n_channels=2)
    assert ex.channel_indices == {'0': (0, 2, 4), '1': (1, 3, 5)}
    assert ex.feature_indices == {'rand': (0, 1, 2, 3), '0': (4, 5)}


def test_fextractor_indices_no_arguments():
    ex = pipeline.FeatureExtractor(
        [('rand', _RandomMultipleFeature(features_per_channel=2)),
         ('0', _NthSampleFeature(0))])
    assert ex.channel_indices == {}
    assert ex.feature_indices == {}


def test_fextractor_indices_no_arguments_inferred():
    ex = pipeline.FeatureExtractor(
        [('rand', _RandomMultipleFeature(features_per_channel=2)),
         ('0', _NthSampleFeature(0))])
    data = np.array([[0, 1, 2, 3, 4],
                     [5, 6, 7, 8, 9]])
    ex.process(data)
    assert ex.channel_indices == {'0': (0, 2, 4), '1': (1, 3, 5)}
    assert ex.feature_indices == {'rand': (0, 1, 2, 3), '0': (4, 5)}


def test_channel_selector():
    fe = pipeline.FeatureExtractor(
        [('0', _NthSampleFeature(0)),
         ('2', _NthSampleFeature(2))],
        channel_names=['channel_1', 'channel_2', 'channel_3'])
    cs = pipeline.ChannelSelector(
        channels=['channel_1', 'channel_3'],
        channel_indices=fe.channel_indices)
    pipe = pipeline.Pipeline([fe, cs])
    data = np.array([[0, 1, 2, 3, 4],
                     [5, 6, 7, 8, 9],
                     [10, 11, 12, 13, 14]])
    truth = np.array([0, 10, 2, 12])
    assert_array_equal(truth, pipe.process(data))


def test_feature_selector():
    fe = pipeline.FeatureExtractor(
        [('N0', _NthSampleFeature(0)),
         ('N2', _NthSampleFeature(2))],
        n_channels=3)
    fs = pipeline.FeatureSelector(
        features=['N2'],
        feature_indices=fe.feature_indices)
    pipe = pipeline.Pipeline([fe, fs])
    data = np.array([[0, 1, 2, 3, 4],
                     [5, 6, 7, 8, 9],
                     [10, 11, 12, 13, 14]])
    truth = np.array([2, 7, 12])
    assert_array_equal(truth, pipe.process(data))


def test_ensure2d_bad_orientation():
    # test exception raise if bad orientation string given
    with pytest.raises(ValueError):
        pipeline.Ensure2D(orientation='something')


def test_ensure2d_row():
    data = rand_data_1d
    b = pipeline.Ensure2D()
    b_exp = pipeline.Ensure2D(orientation='row')

    truth = data[np.newaxis, :]
    assert_array_equal(truth, b.process(data))
    assert_array_equal(truth, b_exp.process(data))


def test_ensure2d_col():
    data = rand_data_1d
    b = pipeline.Ensure2D(orientation='col')

    truth = data[:, np.newaxis]
    assert_array_equal(truth, b.process(data))


def test_estimator():
    class FakeEstimator(object):

        def fit(self, X, y=None):
            pass

        def predict(self, data):
            pass

    block = pipeline.Estimator(FakeEstimator())
    block.estimator.fit(0)
    block.process(0)


def test_transformer():
    class FakeTransformer(object):

        def fit(self, X, y=None):
            pass

        def transform(self, data):
            pass

    block = pipeline.Transformer(FakeTransformer())
    block.transformer.fit(0)
    block.process(0)


def test_minmaxscaler():
    data = rand_data_2d
    min_ = np.min(data, axis=-1)
    max_ = np.max(data, axis=-1)
    block = pipeline.MinMaxScaler(min_=min_, max_=max_)
    data_proc = block.process(rand_data_2d.T)
    assert_equal(np.min(data_proc), 0.)
    assert_equal(np.max(data_proc), 1.)


def test_minmaxscaler_dims():
    data = rand_data_2d
    min_ = np.min(data, axis=-1)
    max_ = np.max(data, axis=-1)
    block = pipeline.MinMaxScaler(min_=min_, max_=max_)

    # Wrong dimensionality
    with pytest.raises(ValueError):
        block.process(np.random.randn(min_.shape[0] + 1))

    # Dimensions mixed up
    with pytest.raises(ValueError):
        block.process(data)

    # Check tht broadcasting works OK
    block.process(np.random.randn(4, 2, min_.shape[0]))


#
# axopy.pipeline.sources tests
#

def test_segment_simple():
    x = np.arange(6)
    segs = list(pipeline.segment(x, 2))
    assert_equal(segs[0], np.array([[0, 1]]))
    assert_equal(segs[1], np.array([[2, 3]]))
    assert len(segs) == 3


def test_segment_overlap():
    x = np.random.randn(100)
    segs = list(pipeline.segment(x, 10, overlap=5))
    assert_equal(segs[0][:, -5:], segs[1][:, :5])


def test_segment_indices_simple():
    segs = list(pipeline.segment_indices(8, 2))
    assert segs == [(0, 2), (2, 4), (4, 6), (6, 8)]


def test_segment_indices_overlap():
    segs = list(pipeline.segment_indices(9, 3, overlap=2))
    assert segs == [(0, 3), (1, 4), (2, 5), (3, 6), (4, 7), (5, 8), (6, 9)]


def test_segment_indices_bad_length():
    with pytest.warns(UserWarning):
        list(pipeline.segment_indices(11, 5))

    with pytest.warns(UserWarning):
        list(pipeline.segment_indices(12, 5, overlap=2))
