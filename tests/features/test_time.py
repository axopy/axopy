import numpy as np
from unittest import TestCase
from numpy.testing import assert_equal
from hcibench.features import MAV, WL, ZC, SSC


class TestMAV(TestCase):

    def setUp(self):
        self.mav = MAV()

    def test(self):
        x = np.array([[0, 2], [0, -4]])
        truth = np.array([1, 2])

        assert_equal(truth[0], self.mav.compute(x[0]))
        assert_equal(truth, self.mav.compute(x))


class TestWL(TestCase):

    def setUp(self):
        self.wl = WL()

    def test(self):
        x = np.array([[0, 1, 1, -1], [-1, 2.4, 0, 1]])
        truth = np.array([3, 6.8])

        assert_equal(truth[0], self.wl.compute(x[0]))
        assert_equal(truth, self.wl.compute(x))


class TestZC(TestCase):

    def setUp(self):
        self.zc_nothresh = ZC()
        self.zc_thresh = ZC(threshold=1)

    def test(self):
        x = np.array([[1, -1, -0.5, 0.2], [1, -1, 1, -1]])
        truth_nothresh = np.array([2, 3])
        truth_thresh = np.array([1, 3])

        assert_equal(truth_nothresh, self.zc_nothresh.compute(x))
        assert_equal(truth_thresh, self.zc_thresh.compute(x))
        assert_equal(truth_thresh[0], self.zc_thresh.compute(x[0]))


class TestSSC(TestCase):

    def setUp(self):
        self.ssc_nothresh = SSC()
        self.ssc_thresh = SSC(threshold=1)

    def test(self):
        x = np.array([[1, 2, 1.1, 2, 1.2], [1, -1, -0.5, -1.2, 2]])
        truth_nothresh = np.array([3, 3])
        truth_thresh = np.array([0, 2])

        assert_equal(truth_nothresh, self.ssc_nothresh.compute(x))
        assert_equal(truth_thresh, self.ssc_thresh.compute(x))
        assert_equal(truth_thresh[0], self.ssc_thresh.compute(x[0]))
