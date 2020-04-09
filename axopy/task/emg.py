"""Some commonly used EMG task implementations."""

import numpy as np
from scipy.signal import butter
from PyQt5.QtWidgets import QDesktopWidget, QMessageBox
from axopy.task import Task
from axopy.gui.emg import EnvelopeCalibrationWidget
from axopy.gui.canvas import Canvas
from axopy import util
from axopy.pipeline import (Pipeline, Windower, Filter, MinMaxScaler,
                            FeatureExtractor, Ensure2D, Callable)
from axopy.features import MeanAbsoluteValue


class EnvelopeCalibration(Task):
    """EMG task channel selection and envelope calibration.

    This task is intended for task channel selection and calibration of EMG
    envelopes. One `EnvelopeCalibrationWidget` is created for each EMG channel,
    which can be used to calibrate the maximum and minimum values for the
    specific channel as well as perform task channel selection. The following
    calibration data will be stored:
        `c_min` : MAV calibration minimum values, array, shape=(n_channels,)
        `c_max` : MAV calibration maximum values, array, shape=(n_channels,)
        `c_select`: Selected task channels, using the ordering provided in
            `task_channels`, array, shape=(n_task_channels,)
    The raw EMG and normalized MAV data will also be stored. If calibration
    values are not provided for some of the channels, the respective MAV data
    will be nan.

    Parameters
    ----------
    channels : list of int
        EMG channel numbers.
    task_channels : list of str
        Task channel names. These will be passed to `EnvelopeCalibrationWidget`
        so that they provided names are offered as options in the dropdown
        menus.
    rate : float
        Sampling rate (in Hz).
    read_length : float
        Size of data chunk in each read operation (in seconds).
    win_size_mav : float
        Size of window used to extract MAV (in seconds).
    win_size_disp : float
        Size of window used for raw EMG data plotting (in seconds).
    win_size_calib : float
        Size of window used for EMG MAV calibration (in seconds). This window
        will be applied after feature extraction.
    filter : boolean, optional (default=False)
        If ``True``, EMG data will be filtered using a Butterworth digital
        filter.
    filter_type : {'lowpass', 'highpass', 'bandpass', None}, optional.
        Filter type. If ``filter`` is ``False``, it will be ignored. Default
        is None.
    filter_order : int, optional (default=None)
        Filter order. If ``filter`` is ``False``, it will be ignored.
    filter_lowcut : float, optional (default=None)
        Filter low cutoff frequency. If ``filter`` is ``False``, it will be
        ignored.
    filter_highcut : float, optional (default=None)
        Filter high cutoff frequency. If ``filter`` is ``False``, it will be
        ignored.
    c_min : array, shape=(n_channels,), optional (default=None)
        If provided, it will be used to initialize the calibration minimum
        values.
    c_max : array, shape=(n_channels,), optional (default=None)
        If provided, it will be used to initialize the calibration maximum
        values.
    c_select : dict, list or array, len=(n_channels), optional
        If provided, it will be used to initialize the calibration selection
        dictionary. It can be either a dictionary with keys matching the
        elements of ``task_channels``, a list or an array. In the latter case,
        the ordering is assumed to match that of ``task_channels``. Default is
        None.
    storage_name : str, optional (default='calibration')
        Name used for storing calibration data.
    verbose : boolean, optional (default=False)
        If ``True``, calibration values and actions will be printed on the
        console.
    kwargs : key, value mappings
        Other keyword arguments are passed through to
        `EnvelopeCalibrationWidget`.

    Attributes
    ----------
    channel_names : list of str
        Channel names.
    _data_cache : array, shape=(n_channels, n_samples)
        Array storing cache MAV (proceesed) data that will be queried when a
        calibration value is updated. A window is used for the data (see
        ``win_size_calib``) as a safety net.
    """
    def __init__(self, channels, task_channels, rate, read_length,
                 win_size_mav, win_size_disp, win_size_calib,
                 filter=False, filter_type=None, filter_order=None,
                 filter_lowcut=None, filter_highcut=None, c_min=None,
                 c_max=None, c_select=None, storage_name='calibration',
                 verbose=False, **kwargs):
        super(EnvelopeCalibration, self).__init__()
        self.channels = channels
        self.task_channels = task_channels
        self.rate = rate
        self.read_length = read_length
        self.win_size_mav = win_size_mav
        self.win_size_disp = win_size_disp
        self.win_size_calib = win_size_calib
        self.filter = filter
        self.filter_type = filter_type
        self.filter_order = filter_order
        self.filter_lowcut = filter_lowcut
        self.filter_highcut = filter_highcut
        self.c_min = c_min
        self.c_max = c_max
        self.c_select = c_select
        self.storage_name = storage_name
        self.verbose = verbose
        self.kwargs = kwargs

        if self.c_min is None:
            self.c_min = np.full(len(self.channels), np.nan)

        if self.c_max is None:
            self.c_max = np.full(len(self.channels), np.nan)

        if self.c_select is None:
            self.c_select = dict()
        else:
            # If dictionary provided, check that keys match task_channels
            if isinstance(self.c_select, dict):
                for task_channel in self.task_channels:
                    if task_channel not in self.c_select.keys():
                        raise ValueError("Task channels and keys in " +
                                         "`c_select` must match.")
            # If list or array, convert to dictionary
            elif isinstance(self.c_select, np.ndarray) or \
                    isinstance(self.c_select, list):
                self.c_select = dict(zip(self.task_channels, self.c_select))

        self.channel_names = ['EMG channel ' + str(channel) for channel
                              in self.channels]
        self._data_cache = None

        self.make_pipelines()
        self.advance_block_key = None

    def make_pipelines(self):
        """There are three pipelines:
            pipeline['scope'] is used to window raw EMG data for plotting them
            pipeline['mav_win']  is used to window MAV (processed) data which
                are queried when calibration values are updated. We use a
                window after MAV extraction as a safety net.
            pipeline['mav_norm'] is used to produce the calibrated (normalized)
                MAV data which are plotted in the bar graphs.
        """
        self.pipeline = {}
        self.make_scope_pipeline()
        self.make_mav_win_pipeline()
        self.make_mav_norm_pipeline()

    def make_scope_pipeline(self):
        windower = Windower(int(self.rate * self.win_size_disp))
        if self.filter:
            filter = self.make_filter(win_size=self.win_size_disp)

        if self.filter:
            self.pipeline['scope'] = Pipeline([windower, filter])
        else:
            self.pipeline['scope'] = Pipeline([windower])

    def make_mav_win_pipeline(self):
        windower_pre = Windower(int(self.rate * self.win_size_mav))
        if self.filter:
            filter = self.make_filter(win_size=self.win_size_mav)

        fe = FeatureExtractor(
            [('MAV', MeanAbsoluteValue())])
        e2d = Ensure2D(orientation='col')
        windower_post = Windower(
            int((1 / self.read_length) * self.win_size_calib))
        if self.filter:
            self.pipeline['mav_win'] = Pipeline([
                windower_pre, filter, fe, e2d, windower_post])
        else:
            self.pipeline['mav_win'] = Pipeline([
                windower_pre, fe, e2d, windower_post])

    def make_mav_norm_pipeline(self):
        windower = Windower(int(self.rate * self.win_size_mav))
        if self.filter:
            filter = self.make_filter(win_size=self.win_size_mav)

        fe = FeatureExtractor(
            [('MAV', MeanAbsoluteValue())])
        mmsc = MinMaxScaler(min_=self.c_min, max_=self.c_max)
        # Calibrated MAV is non-negative, but we allow values larger than 1
        nonneg = Callable(lambda x: np.clip(x, 0.0, None))
        if self.filter:
            self.pipeline['mav_norm'] = Pipeline([
                windower, filter, fe, mmsc, nonneg])
        else:
            self.pipeline['mav_norm'] = Pipeline([
                windower, fe, mmsc, nonneg])

    def make_filter(self, win_size):
        """Makes filter block for specified window size. """
        if self.filter_type == 'lowpass':
            Wn = self.filter_highcut / (self.rate * 0.5)
        elif self.filter_type == 'highpass':
            Wn = self.filter_lowcut / (self.rate * 0.5)
        elif self.filter_type == 'bandpass':
            Wn = [self.filter_lowcut / (self.rate * 0.5),
                  self.filter_highcut / (self.rate * 0.5)]
        else:
            raise ValueError(
                "Invalid or not supported filter type {}.".format(type))

        b, a = butter(N=self.filter_order, Wn=Wn, btype=self.filter_type)
        filter = Filter(b, a, overlap=(int(self.rate * win_size) -
                                       int(self.rate * self.read_length)))
        return filter

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()

    def prepare_design(self, design):
        block = design.add_block()
        block.add_trial()

    def prepare_storage(self, storage):
        self.writer = storage.create_task(self.storage_name)

    def prepare_graphics(self, container):
        self.canvas = Canvas()
        container.set_widget(self.canvas)

        self.init_widgets()

    def init_widgets(self):
        """Initalizes the EMG calibration widgets, one per channel. """
        self.widgets = []

        # Use 0-based indexing for widget id's
        for i, _ in enumerate(self.channels):
            size, pos = self.get_widget_geometry(id=i)
            widget = EnvelopeCalibrationWidget(
                id=i,
                name=self.channel_names[i],
                task_channels=self.task_channels,
                size=size,
                pos=pos,
                **self.kwargs)
            widget.show()
            self.widgets.append(widget)

    def get_widget_geometry(self, id):
        """Computes the size and position for each EMG calibration widget. """
        screen = QDesktopWidget().screenGeometry()
        if len(self.channels) == 1:
            positions = [(0, 0)]
        elif len(self.channels) == 2:
            positions = [(0, 0), (0, 1)]
        else:
            positions = [(i, j) for i in range(2) for j in range(
                int(np.ceil(len(self.channels) / 2)))]

        max_row = positions[-1][0]
        max_col = positions[-1][1]
        w_w = screen.width() / (max_col+1)
        w_h = min([w_w / 2, screen.height() / (max_row+1)])
        size = (w_w, w_h)
        pos = (w_w * positions[id][1], w_h*positions[id][0])

        return (size, pos)

    def run_trial(self, trial):
        # Initialize storage arrays
        trial.add_array('data_raw', stack_axis=1)
        trial.add_array('data_mav', stack_axis=1)
        trial.add_array('c_min', stack_axis=1)
        trial.add_array('c_max', stack_axis=1)
        trial.add_array('c_max', stack_axis=1)
        trial.add_array('c_select', stack_axis=1, dtype=np.int)

        # Connect signals from EMG widgets to appropriate slots
        for widget in self.widgets:
            self.connect(widget.min, self.min_update)
            self.connect(widget.max, self.max_update)
            self.connect(widget.reset, self.reset_update)
            self.connect(widget.active, self.update_widgcols)
            self.connect(widget.selected, self.selection_update)

        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        data_scope = self.pipeline['scope'].process(data)
        data_mav_norm = self.pipeline['mav_norm'].process(data)
        for i, channel_data in enumerate(data_scope):
            self.widgets[i].emgItem.setData(channel_data)

        for i, channel_data in enumerate(data_mav_norm):
            self.widgets[i].barItem.setOpts(height=channel_data)

        # Keep track of windowed mav which is queried during weight updates
        self._data_cache = self.pipeline['mav_win'].process(data)

        # Save data
        self.trial.arrays['data_raw'].stack(data)
        self.trial.arrays['data_mav'].stack(data_mav_norm.reshape(-1, 1))

    def min_update(self, id):
        """Updates a minimum calibration value when a relevant signal is
        received. """
        self.c_min[id] = np.min(self._data_cache[id])
        if self.verbose:
            print("Channel {}, min value updated: {}.".format(
                self.channel_names[id], self.c_min[id]))

        self.update_pipeline_cal_weights()

    def max_update(self, id):
        """Updates a maximum calibration value when a relevant signal is
        received. """
        self.c_max[id] = np.max(self._data_cache[id])
        if self.verbose:
            print("Channel {}, max value updated: {}.".format(
                self.channel_names[id], self.c_max[id]))

        self.update_pipeline_cal_weights()

    def reset_update(self, id):
        """Resets the minimum  and maximum calibration values when a reset
        signal is received. """
        self.c_min[id] = np.nan
        self.c_max[id] = np.nan
        if self.verbose:
            print("Channel {} rest.".format(self.channel_names[id]))

        self.update_pipeline_cal_weights()

    def selection_update(self, selection):
        """Updates the channel selection dictionary when a relevant signal is
        received. """
        id, control = selection
        if control is not None:
            self.c_select[control] = self.channels[id]

        if self.verbose:
            if control is not None:
                print("{} controls {}".format(self.channel_names[id], control))
            else:
                print("{} does unselected.".format(self.channel_names[id]))

    def update_pipeline_cal_weights(self):
        """Updates the pipeline calibration weights. It should be called
        whenever the weights are updated. """
        self.pipeline['mav_norm'].blocks[-2].min = self.c_min
        self.pipeline['mav_norm'].blocks[-2].max = self.c_max

    def update_widgcols(self, id):
        """Updates the raw EMG plot colour for the specified widget.  """
        for widget in self.widgets:
            widget.set_emg_color((120, 120, 120))

        self.widgets[id].set_emg_color('b')

    def key_press(self, key):
        """The only check that is performed on exit (esc) is whether the task
        channels have been successfully assigned. If they haven't, the user
        is prompted that calibration will not be saved should they choose to
        continue. Pressing z on the main window will calibrate all minimum
        values.
        """
        if key == util.key_escape:
            if not self.check_task_channel_selection():
                msg = "Task channels have not been appropriately " + \
                    "selected. If you exit now, calibration will not be " + \
                    "saved. Are you sure you want to continue?"
                reply = QMessageBox.question(
                    self.canvas, 'Message', msg,
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.finish()
                else:
                    pass

            else:
                self.finish_trial()

        if key == util.key_z:
            for id in range(len(self.channels)):
                self.min_update(id)

    def check_task_channel_selection(self):
        """Performs the task channel selection check. """
        for task_channel in self.task_channels:
            if task_channel not in self.c_select:
                return False

        return True

    def finish_trial(self):
        """Store calibration data and exit. """
        self.check_task_channel_selection()
        # Convert c_select to array with same ordering as task_channels
        c_select_ar = np.asarray([self.c_select[i] for i
                                  in self.task_channels])
        # Save calibration data
        self.trial.arrays['c_min'].stack(self.c_min)
        self.trial.arrays['c_max'].stack(self.c_max)
        self.trial.arrays['c_select'].stack(c_select_ar)
        self.writer.write(self.trial)

        self.disconnect(self.daqstream.updated, self.update)
        if self.verbose:
            print("Calibration minimum values\n{}".format(self.c_min))
            print("Calibration maximum values\n{}".format(self.c_max))
            print("Channel selection: {}".format(self.c_select))

        self.finish()

    def finish(self):
        self.daqstream.stop()
        self.finished.emit()
