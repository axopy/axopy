import time
import numpy as np
from expyriment.io._input_output import Input

class MouseInterface(object):

    def __init__(self, mouse, rate=10):
        self.mouse = mouse

        self.rate = rate

        self._t_last_read = None
        self._t_per_read = float(1 / self.rate)

    def start(self):
        pass

    def stop(self):
        pass

    def read(self):
        t = time.time()
        if self._t_last_read is None:
            time.sleep(self._t_per_read)
        else:
            try:
                time.sleep(self._t_per_read - (t - self._t_last_read))
            except ValueError:
                # if we're not meeting real-time requirement, don't wait
                pass

        data = np.asarray(self.mouse.position)

        self._t_last_read = time.time()
        return data


class EmulatedDaq(Input):
    """
    An emulated data acquisition device which generates random data.

    Each sample of the generated data is sampled from a zero-mean Gaussian
    distribution with variance determined by the amplitude specified, which
    corresponds to three standard deviations. That is, approximately 99.7% of
    the samples should be within the desired peak amplitude.

    :class:`EmulatedDaq` is meant to emulate data acquisition devices that
    block on each request for data until the data is available. See
    :meth:`read` for details.

    Parameters
    ----------
    rate : int, optional
        Sample rate in Hz. Default is 1000.
    num_channels : int, optional
        Number of "channels" to generate. Default is 1.
    amplitude : float, optional
        Approximate peak amplitude of the signal to generate. Specifically, the
        amplitude represents three standard deviations for generating the
        Gaussian distributed data. Default is 1.
    read_size : int, optional
        Number of samples to generate per :meth:`read()` call. Default is 100.
    """

    def __init__(self, rate=1000, num_channels=1, amplitude=1.0,
                 read_size=100):
        Input.__init__(self)

        self.rate = rate
        self.num_channels = num_channels
        self.amplitude = amplitude
        self.read_size = read_size

        self._sigma = amplitude / 3

        self._t_last_read = None
        self._t_per_read = float(self.read_size / self.rate)

    def start(self):
        pass

    def read(self):
        """
        Generates zero-mean Gaussian data.

        This method blocks (calls ``time.sleep()``) to emulate other data
        acquisition units which wait for the requested number of samples to be
        read. The amount of time to block is calculated such that consecutive
        calls will always return with constant frequency, assuming the calls
        occur faster than required (i.e. processing doesn't fall behind).

        Returns
        -------
        data : ndarray, shape (num_channels, read_size)
            The generated data.
        """
        t = time.time()
        if self._t_last_read is None:
            time.sleep(self._t_per_read)
        else:
            try:
                time.sleep(self._t_per_read - (t - self._t_last_read))
            except ValueError:
                # if we're not meeting real-time requirement, don't wait
                pass

        data = self._sigma * np.random.randn(self.num_channels, self.read_size)

        self._t_last_read = time.time()
        return data

    def stop(self):
        pass

    def reset(self):
        pass
