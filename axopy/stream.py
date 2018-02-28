"""Threaded interfaces for input and output devices."""

import time
import numpy
from axopy.messaging import transmitter
from PyQt5 import QtCore
from axopy.gui.main import get_qtapp, qt_key_map


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

        self.sleeper = _Sleeper(float(self.read_size/self.rate))

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
        self.sleeper.sleep()
        data = self._sigma * numpy.random.randn(self.num_channels,
                                                self.read_size)
        return data

    def stop(self):
        pass

    def reset(self):
        self.sleeper.reset()


class Keyboard(QtCore.QObject):
    """Keyboard input device.

    The keyboard device works by periodically sampling (with the rate
    specified) whether or not the watched keys have been pressed since the last
    sampling event. The output is a numpy array of shape ``(n_keys, 1)``, where
    the numerical values are booleans indicating whether or not the
    corresponding keys have been pressed.

    Parameters
    ----------
    rate : int, optional
        Sampling rate, in Hz.
    keys : container of str, optional
        Keys watch and use as input signals. The keys used here should not
        conflict with the key used by the ``Experiment`` to start the next
        task.

    Notes
    -----

    There are a couple reasonable alternatives to the way the keyboard device
    is currently implemented. One way to do it might be sampling the key states
    at a given rate and producing segments of sampled key state data, much like
    a regular data acquisition device. One issue is that actual key state
    (whether the key is being physically pressed or not) doesn't seem to be
    feasible to find out with Qt. You can hook into key press and key release
    events, but these are subject to repeat delay and repeat rate.

    Another possible keyboard device would be responsive to key press events
    themselves rather than an input sampling event. While Qt enables
    event-based keyboard handling, the method used here fits the input device
    model, making it easily swappable with other input devices.
    """

    def __init__(self, rate=10, keys=None):
        super(Keyboard, self).__init__()
        self.rate = rate

        if keys is None:
            keys = list('wasd')
        self.keys = keys

        self._qkeys = [qt_key_map[k] for k in keys]

        self._sleeper = _Sleeper(1.0/rate)
        self._data = numpy.zeros((len(self.keys), 1))

    def start(self):
        """Start the keyboard input device."""
        # install event filter to capture keyboard input events
        get_qtapp().installEventFilter(self)

    def read(self):
        """Read which keys have just been pressed.

        Returns
        -------
        data : ndarray, shape (n_keys, 1)
            A boolean array with a 1 indicating the corresponding key has been
            pressed and a 0 indicating it has not.
        """
        self._sleeper.sleep()
        out = self._data.copy()
        self._data *= 0
        return out

    def stop(self):
        """Stop the keyboard input device.

        You may need to stop the device in case you want to be able to use the
        keys watched by the device for another purpose.
        """
        # remove event filter so captured keys propagate when daq isn't used
        get_qtapp().removeEventFilter(self)

    def reset(self):
        self._sleeper.reset()

    def eventFilter(self, obj, event):
        evtype = event.type()
        if evtype == QtCore.QEvent.KeyPress and event.key() in self._qkeys:
            self._data[self._qkeys.index(event.key())] = 1
            return True

        return False


class _Sleeper(object):

    def __init__(self, read_time):
        self.read_time = read_time
        self.last_read_time = None

    def sleep(self):
        t = time.time()
        if self.last_read_time is None:
            time.sleep(self.read_time)
        else:
            try:
                time.sleep(self.read_time - (t - self.last_read_time))
            except ValueError:
                # if we're not meeting real-time requirement, don't wait
                pass

        self._last_read_time = time.time()

    def reset(self):
        self.last_read_time = None
