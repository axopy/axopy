import numpy as np
from scipy import signal

from unittest import TestCase
from numpy.testing import assert_array_equal, assert_array_almost_equal

from hcibench.pipeline import Windower, Filter

np.random.seed(12345)

rand_data_1d = np.random.rand(100, 1)
rand_data_2d = np.random.rand(100, 5)


class TestWindower(TestCase):

    def test_no_overlap(self):
        data = rand_data_2d
        windower = Windower(10, 0)

        for i in range(data.shape[0]//10):
            new_data = windower.process(data[i*10:(i+1)*10, :])

        assert_array_equal(new_data, data[-10:, :])

    def test_overlap(self):
        data = rand_data_2d
        windower = Windower(13, 3)

        for i in range(data.shape[0]//10):
            new_data = windower.process(data[i*10:(i+1)*10, :])

        assert_array_equal(new_data, data[-13:, :])


class TestFilter(TestCase):

    def setUp(self):
        self.b, self.a = signal.butter(
            2, (10/1000, 450/1000), btype='bandpass')

    def test_1d_overlap(self):
        self._do_test(rand_data_1d)

    def test_2d_overlap(self):
        self._do_test(rand_data_2d)

    def _do_test(self, data):
        win_length = 10
        overlap = 5
        block = Filter(self.b, self.a, overlap=overlap)

        data1 = data[0:win_length]
        data2 = data[win_length-overlap:win_length-overlap+win_length]
        out1 = block.process(data1)
        out2 = block.process(data2)

        assert_array_almost_equal(out1[-overlap:], out2[:overlap])
