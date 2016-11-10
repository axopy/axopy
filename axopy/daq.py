import time
import socket
import struct
import numpy as np

try:
    import daqflex
except ImportError:
    pass


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

        data = self._sigma * np.random.randn(self.num_channels, self.read_size)

        self._t_last_read = time.time()
        return data

    def stop(self):
        pass

    def reset(self):
        pass


class MccDaq(object):
    """
    Measurement Computing data acquisition device.

    Use of this class requires `PyDAQFlex
    <https://github.com/torfbolt/PyDAQFlex/>`__.

    For more information, refer to the :ref:`User Guide <mcc_daq>`.

    Parameters
    ----------
    rate : int
        The sampling rate in Hz
    input_range : int
        Input range for the DAQ (+/-) in volts
    channel_range : tuple with 2 ints
        DAQ channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan
    samples_per_read : int
        Number of samples per channel to read in each read operation
    devname : str, optional
        Name of the device as implemented in PyDAQFlex.  Default is
        ``'USB_1608G'``.
    """

    def __init__(self, rate, input_range, channel_range, samples_per_read,
                 devname='USB_1608G'):
        self.rate = rate
        self.input_range = input_range
        self.channel_range = channel_range
        self.samples_per_read = samples_per_read

        self.devname = devname

        self._initialize()

    def _initialize(self):
        self.device = getattr(daqflex, self.devname)()

        self.device.send_message("AISCAN:XFRMODE=BLOCKIO")
        self.device.send_message("AISCAN:SAMPLES=0")
        self.device.send_message("AISCAN:BURSTMODE=ENABLE")
        self.device.send_message("AI:CHMODE=SE")

        self.device.send_message("AISCAN:RATE=%s" % self.rate)
        self.device.send_message("AISCAN:RANGE=BIP%sV" % self.input_range)

        self.set_channel_range(self.channel_range)

    def start(self):
        """
        Starts the DAQ so it begins reading data. read() should be called as
        soon as possible.
        """
        self.device.flush_input_data()
        self.device.send_message("AISCAN:START")

    def read(self):
        """
        Waits for samples_per_read samples to come in, then returns the data
        in a numpy array. The size of the array is (NUM_CHANNELS,
        SAMPLES_PER_READ).
        """
        data = self.device.read_scan_data(
            self.samples_per_read*self.num_channels, self.rate)

        data = np.array(data, dtype=np.float)
        data = np.reshape(data, (-1, self.num_channels)).T
        for i in range(self.num_channels):
            data[i, :] = self.device.scale_and_calibrate_data(
                data[i, :],
                -self.input_range,
                self.input_range,
                self.calibration_data[i])
        data = data / float(self.input_range)

        return data

    def stop(self):
        """
        Stops the DAQ. It needs to be started again before reading.
        """
        try:
            self.device.send_message("AISCAN:STOP")
        except:
            print('warning: DAQ could not be stopped')
            pass

    def set_channel_range(self, channel_range):
        self.channel_range = channel_range

        self.calibration_data = []
        for ch in range(channel_range[0], channel_range[1]+1):
            self.calibration_data.append(self.device.get_calib_data(ch))

        self.num_channels = len(self.calibration_data)

        self.device.send_message(
            "AISCAN:LOWCHAN={0}".format(channel_range[0]))
        self.device.send_message(
            "AISCAN:HIGHCHAN={0}".format(channel_range[1]))


class _BaseTrignoDaq(object):
    """
    Delsys Trigno wireless EMG system.

    Requires the Trigno Control Utility to be running.

    For more information, refer to the :ref:`User Guide <trigno_daq>`.

    Parameters
    ----------
    host : str
        IP address the TCU server is running on.
    cmd_port : int
        Port of TCU command messages.
    data_port : int
        Port of TCU data access.
    rate : int
        Sampling rate of the data source.
    total_channels : int
        Total number of channels supported by the device.

    Attributes
    ----------
    BYTES_PER_CHANNEL : int
        Number of bytes per sample per channel. EMG and accelerometer data
    CMD_TERM : str
        Command string termination.
    CONNECTION_TIMEOUT : int
        Timeout for initializing connection to TCU (in seconds).

    Notes
    -----
    Implementation details can be found in the Delsys SDK reference:
    http://www.delsys.com/integration/sdk/
    """

    BYTES_PER_CHANNEL = 4
    CMD_TERM = '\r\n\r\n'
    CONNECTION_TIMEOUT = 2

    def __init__(self, host, cmd_port, data_port, total_channels):
        self.host = host
        self.cmd_port = cmd_port
        self.data_port = data_port
        self.total_channels = total_channels

        self._min_recv_size = self.total_channels * self.BYTES_PER_CHANNEL

        self._initialize()

    def _initialize(self):

        # create command socket and consume the servers initial response
        self._comm_socket = socket.create_connection(
            (self.host, self.cmd_port), 2)
        self._comm_socket.recv(1024)

        # create the data socket
        self._data_socket = socket.create_connection(
            (self.host, self.data_port), 2)

    def start(self):
        """
        Tell the device to begin streaming data.

        You should call ``read()`` soon after this, though the device typically
        takes about two seconds to send back the first batch of data.
        """
        self._send_cmd('START')

    def read(self, num_samples):
        """
        Request a sample of data from the device.

        This is a blocking method, meaning it returns only once the requested
        number of samples are available.

        Parameters
        ----------
        num_samples : int
            Number of samples to read per channel.

        Returns
        -------
        data : ndarray, shape=(total_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
        """
        l_des = num_samples * self._min_recv_size
        l = 0
        packet = bytes()
        while l < l_des:
            try:
                packet += self._data_socket.recv(l_des - l)
            except socket.timeout:
                l = len(packet)
                packet += b'\x00' * (l_des - l)
                raise DisconnectException
            l = len(packet)

        data = np.asarray(
            struct.unpack('<'+'f'*self.total_channels*num_samples, packet))
        data = np.transpose(data.reshape((-1, self.total_channels)))

        return data

    def stop(self):
        """Tell the device to stop streaming data."""
        self._send_cmd('STOP')

    def reset(self):
        """Restart the connection to the Trigno Control Utility server."""
        self._initialize()

    def __del__(self):
        try:
            self._comm_socket.close()
        except:
            pass

    def _send_cmd(self, command):
        self._comm_socket.send(self._cmd(command))
        resp = self._comm_socket.recv(128)
        self._validate(resp)

    @staticmethod
    def _cmd(command):
        return bytes("{}{}".format(command, _BaseTrignoDaq.CMD_TERM),
                     encoding='ascii')

    @staticmethod
    def _validate(response):
        s = str(response)
        if 'OK' not in s:
            print("warning: TrignoDaq command failed: {}".format(s))


class TrignoEMG(_BaseTrignoDaq):
    """
    Delsys Trigno wireless EMG system EMG data.

    Requires the Trigno Control Utility to be running.

    For more information, refer to the :ref:`User Guide <trigno_daq>`.

    Parameters
    ----------
    channel_range : tuple with 2 ints
        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan. Each sensor has a single EMG
        channel.
    samples_per_read : int
        Number of samples per channel to read in each read operation.
    units : {'V', 'mV', 'normalized'}, optional
        Units in which to return data. If 'V', the data is returned in its
        un-scaled form (volts). If 'mV', the data is scaled to millivolt level.
        If 'normalized', the data is scaled by its maximum level so that its
        range is [-1, 1].
    host : str, optional
        IP address the TCU server is running on. By default, the device is
        assumed to be attached to the local machine.
    cmd_port : int, optional
        Port of TCU command messages.
    data_port : int, optional
        Port of TCU EMG data access. By default, 50041 is used, but it is
        configurable through the TCU graphical user interface.

    Attributes
    ----------
    rate : int
        Sampling rate in Hz.
    scaler : float
        Multiplicative scaling factor to convert the signals to the desired
        units.
    """

    def __init__(self, channel_range, samples_per_read, units='V',
                 host='localhost', cmd_port=50040, data_port=50041):
        super(TrignoEMG, self).__init__(
            host=host, cmd_port=cmd_port, data_port=data_port,
            total_channels=16)

        self.channel_range = channel_range
        self.samples_per_read = samples_per_read

        self.rate = 2000

        self.scaler = 1.
        if units == 'mV':
            self.scaler = 1000.
        elif units == 'normalized':
            # max range of EMG data is 11 mV
            self.scaler = 1 / 0.011

    def set_channel_range(self, channel_range):
        """
        Sets the number of channels to read from the device.

        Parameters
        ----------
        channel_range : tuple
            Sensor channels to use (lowchan, highchan).
        """
        self.channel_range = channel_range
        self.num_channels = channel_range[1] - channel_range[0] + 1

    def read(self):
        """
        Request a sample of data from the device.

        This is a blocking method, meaning it returns only once the requested
        number of samples are available.

        Returns
        -------
        data : ndarray, shape=(num_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
        """
        data = super(TrignoEMG, self).read(self.samples_per_read)
        data = data[self.channel_range[0]:self.channel_range[1]+1, :]
        return self.scaler * data


class TrignoAccel(_BaseTrignoDaq):
    """
    Delsys Trigno wireless EMG system accelerometer data.

    Requires the Trigno Control Utility to be running.

    For more information, refer to the :ref:`User Guide <trigno_daq>`.

    Parameters
    ----------
    channel_range : tuple with 2 ints
        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan. Each sensor has three accelerometer
        channels.
    samples_per_read : int
        Number of samples per channel to read in each read operation.
    host : str, optional
        IP address the TCU server is running on. By default, the device is
        assumed to be attached to the local machine.
    cmd_port : int, optional
        Port of TCU command messages.
    data_port : int, optional
        Port of TCU accelerometer data access. By default, 50042 is used, but
        it is configurable through the TCU graphical user interface.
    """
    def __init__(self, channel_range, samples_per_read, host='localhost',
                 cmd_port=50040, data_port=50042):
        super(TrignoAccel, self).__init__(
            host=host, cmd_port=cmd_port, data_port=data_port,
            total_channels=48)

        self.channel_range = channel_range
        self.samples_per_read = samples_per_read

        self.rate = 148.1

    def set_channel_range(self, channel_range):
        """
        Sets the number of channels to read from the device.

        Parameters
        ----------
        channel_range : tuple
            Sensor channels to use (lowchan, highchan).
        """
        self.channel_range = channel_range
        self.num_channels = channel_range[1] - channel_range[0] + 1

    def read(self):
        """
        Request a sample of data from the device.

        This is a blocking method, meaning it returns only once the requested
        number of samples are available.

        Returns
        -------
        data : ndarray, shape=(num_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
        """
        data = super(TrignoAccel, self).read(self.samples_per_read)
        data = data[self.channel_range[0]:self.channel_range[1]+1, :]
        return data


class DisconnectException(Exception):
    pass
