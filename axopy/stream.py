"""Threaded interfaces for input and output devices."""

import time
import numpy
from axopy.messaging import transmitter
from PyQt5 import QtCore


class InputStream(QtCore.QThread):
    """Asynchronous interface to an input device.

    Wraps an input device
    Runs a persistent while loop wherein the InputStream device is repeatedly
    polled for data. When the data becomes available, it is emitted and the
    loop continues.

    Parameters
    ----------
    device : OutputDevice
        Any object implementing the OutputDevice interface. See EmulatedDaq for
        an example.

    Attributes
    ----------
    updated : pyqtSignal
        Emits the latest data from the data acquisition unit as processed by
        the pipeline.
    disconnected : pyqtSignal
        Emitted when there is a problem with the data acquisition unit.
    """

    def __init__(self, device):
        super(InputStream, self).__init__()
        self.device = device

        self._running = False

    @property
    def running(self):
        return self._running

    def run(self):
        self._running = True

        self.device.start()

        while True:
            if not self._running:
                break

            try:
                d = self.device.read()
            except IOError:
                self.disconnected()
                return

            if self._running:
                self.updated(d)

        self.device.stop()
        self.finished()

    def kill(self, wait=True):
        self._running = False
        if wait:
            self.wait()

    @transmitter(data=object)
    def updated(self, data):
        """Transmitted when the latest chunk of data is available.

        Returns
        -------
        data : object
            Data from the underlying device. See the device's documentation for
            the ``read`` method.
        """
        return data

    @transmitter()
    def disconnected(self):
        return

    @transmitter()
    def finished(self):
        return


class EmulatedDaq(object):
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

        data = self._sigma * numpy.random.randn(self.num_channels,
                                                self.read_size)

        self._t_last_read = time.time()
        return data

    def stop(self):
        pass

    def reset(self):
        pass
