import pytest
import numpy as np
from numpy.testing import assert_equal
import axopy.features as features


@pytest.fixture
def array_2d():
    return np.array([[1, 2, 3, 4], [5, 6, 7, 8]])


@pytest.fixture
def array_1d():
    return np.array([1, 2, 3, 4, 5])


def test_ensure_2d(array_1d, array_2d):
    assert_equal(features.util.ensure_2d(array_2d), array_2d)
    assert features.util.ensure_2d(array_1d).ndim == 2


@pytest.mark.parametrize('func', [
    features.util.inverted_t_window,
    features.util.trapezoidal_window,
])
def test_window_func_length(func):
    w = func(10)
    assert len(w) == 10


def test_rolling_window_1d(array_1d):
    out = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
    assert_equal(features.util.rolling_window(array_1d, 2), out)


def test_rolling_window_2d(array_2d):
    out = np.array([[[1, 2], [2, 3], [3, 4]], [[5, 6], [6, 7], [7, 8]]])
    assert_equal(features.util.rolling_window(array_2d, 2), out)


def test_inverted_t_window():
    # default params (n = 8)
    truth = np.array([0.5, 1, 1, 1, 1, 1, 0.5, 0.5])
    w = features.util.inverted_t_window(8)
    assert_equal(w, truth)

    # different amplitude (n = 9)
    truth = np.array([0.3, 0.3, 1, 1, 1, 1, 0.3, 0.3, 0.3])
    w = features.util.inverted_t_window(9, a=0.3)
    assert_equal(w, truth)

    # different notch time (n = 100)
    truth = np.hstack([9*[0.5], np.ones(100-19), 10*[0.5]])
    w = features.util.inverted_t_window(100, p=0.1)
    assert_equal(w, truth)


def test_trapezoidal_window():
    # default params
    truth = np.array([0.5, 1, 1, 1, 1, 1, 0.5, 0])
    w = features.util.trapezoidal_window(8)
    assert_equal(w, truth)

    # non-default ramp time
    truth = np.array([1/3., 2/3., 1, 1, 1, 1, 2/3., 1/3., 0])
    w = features.util.trapezoidal_window(9, p=1/3.)
    assert_equal(w, truth)


@pytest.mark.parametrize('func', [
    features.mean_absolute_value,
    features.waveform_length,
    features.zero_crossings,
    features.slope_sign_changes,
    features.root_mean_square,
    features.integrated_emg,
    features.logvar
])
def test_feature_io(func):
    """Make sure feature function gets 1D and 2D IO correct."""
    n = 10
    c = 3
    x_n = np.random.randn(n)
    x_cn = np.random.randn(c, n)
    x_nc = np.random.randn(n, c)

    assert not isinstance(func(x_n), np.ndarray)  # scalar
    assert func(x_n, keepdims=True).shape == (1,)
    assert func(x_cn).shape == (c,)
    assert func(x_cn, keepdims=True).shape == (c, 1)
    assert func(x_nc, axis=0).shape == (c,)
    assert func(x_nc, axis=0, keepdims=True).shape == (1, c)


def test_mav():
    x = np.array([[0, 2], [0, -4]])
    truth = np.array([1, 2])

    assert_equal(features.mean_absolute_value(x), truth)


def test_mav1():
    x = np.vstack([np.ones(8), np.zeros(8)])
    # weights should be [0.5, 1, 1, 1, 1, 1, 0.5, 0.5]
    truth = np.array([0.8125, 0])
    assert_equal(features.mean_absolute_value(x, weights='mav1'), truth)


def test_mav2():
    x = np.vstack([np.ones(8), np.zeros(8)])
    # weights should be [0.5, 1, 1, 1, 1, 1, 0.5, 0]
    truth = np.array([0.75, 0])
    assert_equal(features.mean_absolute_value(x, weights='mav2'), truth)


def test_mav_custom_weights():
    x = np.ones((4, 10))
    w = np.zeros(x.shape[1])
    w[0:2] = 0.4
    truth = (2*0.4/x.shape[1])*np.ones(x.shape[0])

    assert_equal(features.mean_absolute_value(x, weights=w), truth)


def test_mav_bad_weights():
    # weights not one of the built-in types of MAV
    with pytest.raises(ValueError):
        features.mean_absolute_value(np.zeros(2), weights='asdf')


def test_mav_bad_custom_weights():
    # custom weights not the same length as the input data
    x = np.zeros((4, 10))
    w = np.zeros(5)
    with pytest.raises(ValueError):
        features.mean_absolute_value(x, weights=w)


def test_wl():
    x = np.array([[0, 1, 1, -1], [-1, 2.4, 0, 1]])
    truth = np.array([3, 6.8])

    assert_equal(features.waveform_length(x), truth)


def test_zc():
    x = np.array([[1, -1, -0.5, 0.2], [1, -1, 1, -1]])

    # zero threshold
    truth_nothresh = np.array([2, 3])
    assert_equal(features.zero_crossings(x), truth_nothresh)

    # threshold of 1
    truth_thresh = np.array([1, 3])
    assert_equal(features.zero_crossings(x, threshold=1), truth_thresh)


def test_ssc():
    x = np.array([[1, 2, 1.1, 2, 1.2], [1, -1, -0.5, -1.2, 2]])

    # zero threshold
    truth_nothresh = np.array([3, 3])
    assert_equal(features.slope_sign_changes(x), truth_nothresh)

    # threshold of one
    truth_thresh = np.array([0, 2])
    assert_equal(features.slope_sign_changes(x, threshold=1), truth_thresh)


def test_rms():
    x = np.array([[1, -1, 1, -1], [2, 4, 0, 0]])
    truth = np.array([1., np.sqrt(5)])

    assert_equal(features.root_mean_square(x), truth)


def test_integrated_emg():
    x = np.array([[-1., 1., -1.], [0, 0, 0]])
    truth = np.array([3.0, 0])

    assert_equal(features.integrated_emg(x), truth)


def test_logvar():
    features.logvar(np.random.randn(100))
    features.logvar(np.random.randn(2, 100))
