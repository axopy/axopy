import numpy as np
from unittest import TestCase
from numpy.testing import assert_equal
from hcibench.features import MAV, WL, ZC, SSC


class TestMAV(TestCase):

    def test_mav(self):
        mav = MAV()
        x = np.array([[0, 2], [0, -4]])
        truth = np.array([1, 2])

        _assert_match(truth, mav, x)

    def test_mav1(self):
        mav = MAV(weights='mav1')

        x = np.zeros(8)
        mav.compute(x)
        weights = np.array([0.5, 1, 1, 1, 1, 1, 0.5, 0.5])
        assert_equal(mav._w, weights)

        x = np.zeros(9)
        mav.compute(x)
        weights = np.array([0.5, 0.5, 1, 1, 1, 1, 0.5, 0.5, 0.5])
        assert_equal(mav._w, weights)

    def test_mav2(self):
        mav = MAV(weights='mav2')

        x = np.zeros(8)
        mav.compute(x)
        weights = np.array([0.5, 1, 1, 1, 1, 1, 0.5, 0])
        assert_equal(mav._w, weights)

        x = np.zeros(9)
        mav.compute(x)
        weights = np.array([4/9., 8/9., 1, 1, 1, 1, 8/9., 4/9., 0])
        assert_equal(mav._w, weights)

    def test_custom_weights(self):
        x = np.ones((4, 10))
        w = np.zeros(x.shape[1])
        w[0:2] = 0.4
        mav = MAV(weights=w)
        truth = (2*0.4/x.shape[1])*np.ones(x.shape[0])
        _assert_match(truth, mav, x)

    def test_bad_custom_weights(self):
        x = np.zeros((4, 10))
        w = np.zeros(5)
        mav = MAV(weights=w)
        with self.assertRaises(ValueError):
            mav.compute(x)

    def test_bad_weights(self):
        mav = MAV(weights='asdf')
        with self.assertRaises(ValueError):
            mav.compute(np.zeros((3, 10)))


class TestWL(TestCase):

    def test(self):
        wl = WL()
        x = np.array([[0, 1, 1, -1], [-1, 2.4, 0, 1]])
        truth = np.array([3, 6.8])

        _assert_match(truth, wl, x)


class TestZC(TestCase):

    def setUp(self):
        self.zc_nothresh = ZC()
        self.zc_thresh = ZC(threshold=1)

    def test(self):
        x = np.array([[1, -1, -0.5, 0.2], [1, -1, 1, -1]])
        truth_nothresh = np.array([2, 3])
        truth_thresh = np.array([1, 3])

        _assert_match(truth_nothresh, self.zc_nothresh, x)
        _assert_match(truth_thresh, self.zc_thresh, x)


class TestSSC(TestCase):

    def setUp(self):
        self.ssc_nothresh = SSC()
        self.ssc_thresh = SSC(threshold=1)

    def test(self):
        x = np.array([[1, 2, 1.1, 2, 1.2], [1, -1, -0.5, -1.2, 2]])
        truth_nothresh = np.array([3, 3])
        truth_thresh = np.array([0, 2])

        _assert_match(truth_nothresh, self.ssc_nothresh, x)
        _assert_match(truth_thresh, self.ssc_thresh, x)


def _assert_match(truth, feature, data):
    """Numerically checks input/output with both 2D and 1D input arrays."""
    assert_equal(truth, feature.compute(data))
    assert_equal(truth[0], feature.compute(data[0]))
