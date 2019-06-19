"""
Glove regression.

During calibration phase, the participant is asked to reproduce a series of
postures presented on the screen. Data are collected and stored so that
they can be used later to train models. Data are recorded from Trigno and
Cyberglove in async fahsion (see example ``async_daqs``).

During real-time decoding, the user is prompted to reproduce postures again
and predictions are displayed on the screen.

The following input devices are supported (mutually exclusive):

trigno
    Trigno EMG system.
myo
    Myo armband.
noise
    Noise generator.

All configuration settings are stored and loaded from an external configuration
file (``config.ini``).
"""

import os
import time
import joblib
import numpy as np

from argparse import ArgumentParser
from configparser import ConfigParser
from scipy.signal import butter

from axopy.daq import DumbDaq
from axopy.experiment import Experiment
from axopy.task import Task
from axopy import util
from axopy.timing import Counter, Timer
from axopy.gui.canvas import Canvas
from axopy.pipeline import (Callable, Windower, Filter, Pipeline,
                            FeatureExtractor, Ensure2D, Transformer)
from axopy.gui.prompts import ImagePrompt
from axopy.gui.graph import BarWidget
from axopy.features import mean_value

from features import (WaveformLength, LogVar, AR, WilsonAmplitude,
                      SlopeSignChanges)

from cyberglove import CyberGlove


class _BaseTask(Task):
    """Base experimental task.

    Implements the processing pipeline and the trial counter.

    Warning: This class should not be used directly.
    Use derived classes instead.
    """

    def __init__(self):
        super(_BaseTask, self).__init__()
        # This is where the data from the multiple streams will be stored
        # after they have been processed.
        self.cur_data = {'emg': None, 'glove': None}

    def make_emg_pipeline(self):
        b, a = butter(FILTER_ORDER,
                      (LOWPASS/EMG_S_RATE/2., HIGHPASS/EMG_S_RATE/2.),
                      'bandpass')
        pipeline = Pipeline([
            Windower(int(EMG_S_RATE * WIN_SIZE)),
            Filter(b, a=a,
                   overlap=(int(EMG_S_RATE * WIN_SIZE) -
                            int(EMG_S_RATE * READ_LENGTH))),
            FeatureExtractor([('wl', WaveformLength()),
                              ('logvar', LogVar()),
                              ('ar', AR(order=AR_ORDER)),
                              ('ssc', SlopeSignChanges(threshold=SSC_TH)),
                              ('wamp', WilsonAmplitude(threshold=WAMP_TH))]),
            Ensure2D(orientation='col')
        ])

        return pipeline

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream

        # Set trial length
        self.timer = Counter(
            int(TRIAL_LENGTH / READ_LENGTH))  # daq read cycles
        self.timer.timeout.connect(self.finish_trial)

        self.daqstream['master'].start()
        self.daqstream['emg'].start()
        self.daqstream['glove'].start()
        time.sleep(2) # Wait until everythin has started streaming

    def run_trial(self, trial):
        self.reset()

        trial.add_array('emg_raw', stack_axis=1)
        trial.add_array('emg_proc', stack_axis=1)
        trial.add_array('glove_raw', stack_axis=1)
        trial.add_array('glove_proc', stack_axis=1)

        self.connect_all()

    def connect_all(self):
        self.connect(self.daqstream['master'].updated, self.update_master)
        self.connect(self.daqstream['emg'].updated, self.update_emg)
        self.connect(self.daqstream['glove'].updated, self.update_glove)

    def disconnect_all(self):
        self.disconnect(self.daqstream['master'].updated, self.update_master)
        self.disconnect(self.daqstream['emg'].updated, self.update_emg)
        self.disconnect(self.daqstream['glove'].updated, self.update_glove)

    def reset(self):
        self.timer.reset()
        self.cur_data = {'emg': None, 'glove': None}

    def update_emg(self, data):
        data_proc = self.pipeline['emg'].process(data)
        self.cur_data['emg'] = data_proc

        self.trial.arrays['emg_raw'].stack(data)

    def update_glove(self, data):
        data_proc = self.pipeline['glove'].process(data)
        self.cur_data['glove'] = data_proc

        self.trial.arrays['glove_raw'].stack(data)

    def key_press(self, key):
        super(_BaseTask, self).key_press(key)
        if key == util.key_escape:
            self.finish()

    def finish(self):
        self.daqstream['master'].stop()
        self.daqstream['emg'].stop()
        self.daqstream['glove'].stop()
        self.finished.emit()

    def image_path(self, grip):
        """Returns the path for specified grip. """
        path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'pics',
            grip + '.jpg')
        return path


class DataCollection(_BaseTask):
    """Data collection task.

    Collects training data while participants replicates target postures
    presented to them on the screen.
    """
    def __init__(self):
        super(DataCollection, self).__init__()
        self.pipeline = {
            'emg': self.make_emg_pipeline(),
            'glove': self.make_glove_pipeline()
        }

    def make_glove_pipeline(self):
        pipeline = Pipeline([
            Windower(int(GLOVE_S_RATE * WIN_SIZE)),
            Callable(mean_value),
            Callable(lambda x: np.dot(x, GLOVE_FINGER_MAP)),
            Ensure2D(orientation='col')
        ])

        return pipeline

    def prepare_design(self, design):
        # Each block is one movement and has N_TRIALS repetitions
        for movement in MOVEMENTS:
            block = design.add_block()
            for trial in range(N_TRIALS):
                block.add_trial(attrs={
                    'movement': movement
                })

    def prepare_graphics(self, container):
        self.canvas = Canvas()
        self.image = ImagePrompt()
        self.image.set_image(self.image_path('rest'))
        self.image.show()
        container.set_widget(self.canvas)

    def prepare_storage(self, storage):
        self.writer = storage.create_task('calibration')

    def run_trial(self, trial):
        super(DataCollection, self).run_trial(trial)

        self.image.set_image(self.image_path(trial.attrs['movement']))
        self.image.show()

    def update_master(self):
        # This the "master" Daq, i.e. an update happens when master daq is
        # updated. The check is used to ensure that updates start only after
        # the two streams have started providing data.
        if not any(elem is None for elem in self.cur_data.values()):
            emg_data = self.cur_data['emg'].copy()
            glove_data = self.cur_data['glove'].copy()

            self.trial.arrays['emg_proc'].stack(emg_data)
            self.trial.arrays['glove_proc'].stack(glove_data)

            self.timer.increment()

    def finish_trial(self):
        self.image.set_image(self.image_path('rest'))
        self.image.show()
        self.writer.write(self.trial)

        self.disconnect_all()

        self.wait_timer = Timer(TRIAL_INTERVAL)
        self.wait_timer.timeout.connect(self.next_trial)
        self.wait_timer.start()


class RealTimeControl(_BaseTask):
    """Real-time decoding.

    Parameters
    ----------
    subject : str
        Subject ID.
    hand_control : bool
        If True, the Robolimb will be controlled in real-time.
    display_output : bool
        If True, the prediction will be displayed on the screen.
    """
    def __init__(self, subject):
        super(RealTimeControl, self).__init__()
        self.advance_block_key = util.key_return

        self.subject = subject

        self.load_models()
        self.pipeline = {
            'emg': self.make_emg_pipeline(),
            'glove': self.make_glove_pipeline()
        }
        self.prediction_pipeline = self.make_prediction_pipeline()

    def load_models(self):
        root_models = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'data', self.subject, 'models')
        self.mdl = joblib.load(os.path.join(root_models, 'mdl'))
        self.smoothing = joblib.load(
            os.path.join(root_models, 'smoothing'))
        self.target_scaler = joblib.load(
            os.path.join(root_models, 'target_scaler'))

    def make_glove_pipeline(self):
        pipeline = Pipeline([
            Windower(int(GLOVE_S_RATE * WIN_SIZE)),
            Callable(mean_value),
            Callable(lambda x: np.dot(x, GLOVE_FINGER_MAP)),
            Ensure2D(orientation='row'),
            Transformer(self.target_scaler),
            Callable(lambda x: x.T),
            Callable(np.clip, func_kwargs={'a_min': 0., 'a_max': 1.})
        ])

        return pipeline

    def make_prediction_pipeline(self):
        """
        Prediction pipeline.

        The input is transposed to match sklearn expected style. The prediction
        is smoothed and clipped in the range [0, 1].
        """
        pipeline = Pipeline([
            Callable(lambda x: np.transpose(x)),
            Callable(self.mdl.predict),
            Ensure2D(orientation='row'),
            Transformer(self.smoothing),
            Callable(np.clip, func_kwargs={'a_min': 0., 'a_max': 1.})
        ])

        return pipeline

    def prepare_design(self, design):
        # Single free run for specified time
        block = design.add_block()
        block.add_trial()

    def prepare_graphics(self, container):

        channel_names = ['DOF ' + str(i) for i in range(1, N_DOF+1)]
        group_colors = ['#1f77b4', '#d62728']
        self.bar = BarWidget(channel_names, group_colors)
        container.set_widget(self.bar)

    def prepare_storage(self, storage):
        self.writer = storage.create_task('control')

    def run_trial(self, trial):
        self.reset()

        trial.add_array('emg_raw', stack_axis=1)
        trial.add_array('emg_proc', stack_axis=1)
        trial.add_array('glove_raw', stack_axis=1)
        trial.add_array('glove_proc', stack_axis=1)
        trial.add_array('glove_pred', stack_axis=1)

        self.connect_all()

    def update_master(self, data):
        # This the "master" Daq, i.e. an update happens when master daq is
        # updated. The check is used to ensure that updates start only after
        # the two streams have started providing data.
        if not any(elem is None for elem in self.cur_data.values()):
            emg_data = self.cur_data['emg'].copy()
            glove_data = self.cur_data['glove'].copy()

            self.trial.arrays['emg_proc'].stack(emg_data)
            self.trial.arrays['glove_proc'].stack(glove_data)

            glove_pred = self.prediction_pipeline.process(emg_data)
            self.trial.arrays['glove_pred'].stack(glove_pred)

            self.bar.plot(np.concatenate(
                (glove_data.reshape(-1,1), glove_pred.reshape(-1,1)),
                axis=1))


            self.timer.increment()

    def finish_trial(self):
        self.writer.write(self.trial)

        self.disconnect_all()


if __name__ == '__main__':
    subject = 'test'

    parser = ArgumentParser()
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument('--train', action='store_true')
    task.add_argument('--test', action='store_true')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--trigno', action='store_true')
    source.add_argument('--myo', action='store_true')
    source.add_argument('--noise', action='store_true')
    args = parser.parse_args()

    cp = ConfigParser()
    cp.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'config.ini'))
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    CHANNELS = list(map(int, (cp.get('hardware', 'channels').split(','))))
    GLOVE_PORT = cp.get('hardware', 'glove_port')
    N_DOF = cp.getint('hardware', 'n_dof')
    WIN_SIZE = cp.getfloat('processing', 'win_size')
    LOWPASS = cp.getfloat('processing', 'lowpass')
    HIGHPASS = cp.getfloat('processing', 'highpass')
    FILTER_ORDER = cp.getfloat('processing', 'filter_order')
    AR_ORDER = cp.getint('features', 'ar_order')
    SSC_TH = cp.getfloat('features', 'ssc_th')
    WAMP_TH = cp.getfloat('features', 'wamp_th')

    MOVEMENTS = cp.get('experiment', 'movements').split(',')

    GLOVE_S_RATE = 40.
    GLOVE_FINGER_MAP = np.loadtxt(
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     'map.csv'),
        delimiter=',')

    cal_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'data', subject, 'glove_calibration.cal')

    if args.trigno:
        from pytrigno import TrignoEMG
        EMG_S_RATE = 2000.
        dev_emg = TrignoEMG(channels=CHANNELS,
                            samples_per_read=int(EMG_S_RATE * READ_LENGTH))
    elif args.myo:
        import myo
        from myo.daq import MyoDaqEMG
        CHANNELS = range(8)
        EMG_S_RATE = 200.
        myo.init(
            sdk_path=r'C:\Users\nak142\Coding\myo-python\myo-sdk-win-0.9.0')
        dev_emg = MyoDaqEMG(channels=CHANNELS,
                            samples_per_read=int(EMG_S_RATE * READ_LENGTH))
    elif args.noise:
        from axopy.daq import NoiseGenerator
        EMG_S_RATE = 2000.
        dev_emg = NoiseGenerator(rate=EMG_S_RATE, num_channels=9,
                                 amplitude=1e-6,
                                 read_size=int(EMG_S_RATE * READ_LENGTH))

    dev_glove = CyberGlove(n_df=18, s_port=GLOVE_PORT, cal_path=cal_path,
                           samples_per_read=1)
    dev_master = DumbDaq(rate=EMG_S_RATE,
                         read_size=int(EMG_S_RATE * READ_LENGTH))
    daq = {'master': dev_master, 'emg': dev_emg, 'glove': dev_glove}

    exp = Experiment(daq=daq, subject=subject, allow_overwrite=True)

    if args.train:
        N_TRIALS = cp.getint('calibration', 'n_trials')
        N_BLOCKS = len(MOVEMENTS)
        TRIAL_LENGTH = cp.getfloat('calibration', 'trial_length')
        TRIAL_INTERVAL = cp.getfloat('calibration', 'trial_interval')



        exp.run(DataCollection())

    elif args.test:
        N_TRIALS = len(MOVEMENTS)
        TRIAL_LENGTH = cp.getfloat('control', 'trial_length')
        exp.run(RealTimeControl(subject=exp.subject))
