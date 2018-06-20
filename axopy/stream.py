"""Threaded interfaces for input and output devices."""

import time
import numpy
from PyQt5 import QtCore
from axopy.messaging import Transmitter
from axopy.gui.main import get_qtapp, qt_key_map
from axopy.pipeline import Filter


class InputStream(QtCore.QThread):
    """Asynchronous interface to an input device.

    Runs a persistent while loop wherein the device is repeatedly polled for
    data. When the data becomes available, it is emitted and the loop
    continues.

    Parameters
    ----------
    device : InputDevice
        Any object implementing the OutputDevice interface. See
        :class:`NoiseGenerator` for an example.

    Attributes
    ----------
    updated : Transmitter
        Transmitted when the latest chunk of data is available. The data type
        depends on the underlying input device, but it is often a numpy
        ndarray.
    disconnected : Transmitter
        Transmitted if the device cannot be read from (it has disconnected
        somehow).
    finished : Transmitter
        Transmitted when the device has stopped and samping is finished.
    """

    updated = Transmitter(object)
    disconnected = Transmitter()
    finished = Transmitter()

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
                self.disconnected.emit()
                return

            if self._running:
                self.updated.emit(d)

        self.device.stop()
        self.finished.emit()

    def kill(self, wait=True):
        self._running = False
        if wait:
            self.wait()


class NoiseGenerator(object):
    """
    An emulated data acquisition device which generates random data.

    Each sample of the generated data is sampled from a zero-mean Gaussian
    distribution with variance determined by the amplitude specified, which
    corresponds to three standard deviations. That is, approximately 99.7% of
    the samples should be within the desired peak amplitude.

    :class:`NoiseGenerator` is meant to emulate data acquisition devices that
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
        Keys to watch and use as input signals. The keys used here should not
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
        """Reset the input device."""
        self._sleeper.reset()

    def eventFilter(self, obj, event):
        evtype = event.type()
        if evtype == QtCore.QEvent.KeyPress and event.key() in self._qkeys:
            self._data[self._qkeys.index(event.key())] = 1
            return True

        return False


class Mouse(QtCore.QObject):
    """Mouse input device.

    The mouse device works by periodically sampling (with the rate specified)
    the mouse position within the AxoPy experiment window. The output is in the
    form of a numpy array of shape ``(2, 1)``, representing either the change
    in position (default) or the absolute position in the window.

    Parameters
    ----------
    rate : int, optional
        Sampling rate, in Hz.
    position : bool, optional
        Whether or not to return the mouse's position (instead of the position
        difference from the prevoius sample).

    Notes
    -----
    In Qt's coordinate system, the positive y direction is *downward*. Here,
    this is inverted as a convenience (upward movement of the mouse produces a
    positive "velocity").

    Mouse events are intercepted here but they are not *consumed*, meaning you
    can still use the mouse to manipulate widgets in the experiment window.
    """

    def __init__(self, rate=10, position=False):
        super(Mouse, self).__init__()
        self.rate = rate
        self._sleeper = _Sleeper(1.0/rate)

        if position:
            b = 1
        else:
            b = (1, -1)
        self._filter = Filter(b)

        self.reset()

    def start(self):
        """Start sampling mouse movements."""
        get_qtapp().installEventFilter(self)

    def read(self):
        """Read the last-updated mouse position.

        Returns
        -------
        data : ndarray, shape (2, 1)
            The mouse "velocity" or position (x, y).
        """
        self._sleeper.sleep()
        return self._filter.process(self._data.copy())

    def stop(self):
        """Stop sampling mouse movements."""
        get_qtapp().removeEventFilter(self)

    def reset(self):
        """Clear the input device."""
        self._data = numpy.zeros((2, 1), dtype=float)
        self._filter.clear()
        self._sleeper.reset()

    def eventFilter(self, obj, event):
        evtype = event.type()
        if evtype == QtCore.QEvent.MouseMove:
            self._data[0] = event.x()
            self._data[1] = -event.y()
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
