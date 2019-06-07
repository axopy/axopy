"""
EMG grip classification.

During calibration phase, the participant is asked to reproduce a series of
postures presented on the screen. Data are collected and stored so that
they can be used later to train models.

During real-time decoding, the user is prompted to reproduce postures again
and they can choose whether predictions should be sent as grip  commands to the
Robolimb hand (if available), be displayed on the screen or both.

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
import joblib
import numpy as np

from argparse import ArgumentParser
from configparser import ConfigParser
from scipy.signal import butter

from axopy.experiment import Experiment
from axopy.task import Task
from axopy import util
from axopy.timing import Counter, Timer
from axopy.gui.canvas import Canvas, Text
from axopy.pipeline import (Callable, Windower, Filter, Pipeline,
                            FeatureExtractor, Ensure2D, Estimator)
from axopy.messaging import Transmitter
from axopy.gui.prompts import ImagePrompt

from features import WaveformLength, LogVar
from hand import RoboLimbGrip


class _BaseTask(Task):
    """Base experimental task.

    Implements the processing pipeline, the daqstream and the trial counter.
    """

    def __init__(self):
        super(_BaseTask, self).__init__()
        self.pipeline = self.make_pipeline()

    def make_pipeline(self):
        # Multiple feature extraction could also be implemented using a
        # parallel pipeline and a block that joins multiple outputs.
        b, a = butter(FILTER_ORDER, (LOWPASS/S_RATE/2., HIGHPASS/S_RATE/2.),
                      'bandpass')
        pipeline = Pipeline([
            Windower(int(S_RATE * WIN_SIZE)),
            Filter(b, a=a,
                   overlap=(int(S_RATE * WIN_SIZE) -
                            int(S_RATE * READ_LENGTH))),
            FeatureExtractor([('wl', WaveformLength()), ('logvar', LogVar())]),
            Ensure2D(orientation='col')
        ])

        return pipeline

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()

        # Set trial length
        self.timer = Counter(
            int(TRIAL_LENGTH / READ_LENGTH))  # daq read cycles
        self.timer.timeout.connect(self.finish_trial)

    def reset(self):
        self.timer.reset()

    def key_press(self, key):
        super(_BaseTask, self).key_press(key)
        if key == util.key_escape:
            self.finish()

    def finish(self):
        self.daqstream.stop()
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
        self.text = Text(text='', color='black')
        self.image = ImagePrompt()
        self.image.set_image(self.image_path('rest'))
        self.image.show()
        self.canvas.add_item(self.text)
        container.set_widget(self.canvas)

    def prepare_storage(self, storage):  # TODO
        self.writer = storage.create_task('calibration')

    def run_trial(self, trial):
        self.reset()
        self.image.set_image(self.image_path(trial.attrs['movement']))
        self.image.show()
        self.text.qitem.setText("{}".format(
            trial.attrs['movement']))
        trial.add_array('data_raw', stack_axis=1)
        trial.add_array('data_proc', stack_axis=1)

        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        data_proc = self.pipeline.process(data)
        # Update Arrays
        self.trial.arrays['data_raw'].stack(data)
        self.trial.arrays['data_proc'].stack(data_proc)

        self.timer.increment()

    def finish_trial(self):
        # self.pic.hide()
        self.text.qitem.setText("{}".format('relax'))
        self.image.set_image(self.image_path('rest'))
        self.image.show()
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.update)

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

    grip = Transmitter(object)

    def __init__(self, subject, hand_control, display_output):
        super(RealTimeControl, self).__init__()
        self.advance_block_key = util.key_return

        self.subject = subject
        self.hand_control = hand_control
        self.display_output = display_output

        self.load_models()
        self.prediction_pipeline = self.make_prediction_pipeline()

        if self.hand_control:
            self.robolimb = RoboLimbGrip()
            self.robolimb.start()
            self.robolimb.open_all()

    def load_models(self):
        root_models = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'data', self.subject, 'models')
        self.mdl = joblib.load(os.path.join(root_models, 'mdl'))
        self.rt = joblib.load(os.path.join(root_models, 'roc_thresholds'))

    def make_prediction_pipeline(self):
        """
        Prediction pipeline.

        The input is first transposed to match sklearn expected style. Then the
        ``predict_proba`` method of the estimator is used. The final step of
        the pipeline consists of a parallel implementation which outputs
        the predicted label, the associated probability and posterior
        probability vector.
        """
        pipeline = Pipeline([
            Callable(lambda x: np.transpose(x)),  # Transpose
            Estimator(self.mdl, return_proba=True),
            (
                Callable(lambda x: self.mdl.classes_[np.argmax(x)]),  # pred
                Callable(lambda x: np.max(x)),  # proba_max
                Callable(lambda x: x)  # proba
            )
        ])

        return pipeline

    def prepare_design(self, design):
        # Each block includes all movements exactly once
        for _ in range(N_BLOCKS):
            block = design.add_block()
            for movement in MOVEMENTS:
                block.add_trial(attrs={
                    'movement': movement
                })
            block.shuffle()

    def prepare_graphics(self, container):
        self.canvas = Canvas()

        self.text_target = Text(text='', color='black')
        self.text_target.pos = (-0.3, 0.3)

        self.text_relax = Text(text='', color='black')
        self.text_relax.qitem.setText('relax')
        self.text_relax.pos = (-0.1, 0.1)
        self.text_relax.hide()

        if self.display_output:
            self.text_prediction = Text(text='', color='red')
            self.text_prediction.pos = (-0.35, 0.0)

        self.canvas.add_item(self.text_target)
        if self.display_output:
            self.canvas.add_item(self.text_prediction)
        self.canvas.add_item(self.text_relax)
        container.set_widget(self.canvas)

    def prepare_storage(self, storage):  # TODO
        self.writer = storage.create_task('control')

    def run_trial(self, trial):
        self.reset()

        self.text_target.qitem.setText("Target: {}".format(
            trial.attrs['movement']))
        trial.add_array('data_raw', stack_axis=1)
        trial.add_array('data_proc', stack_axis=1)
        trial.add_array('prediction', stack_axis=1)
        trial.add_array('prediction_proba', stack_axis=0)
        if self.hand_control:
            trial.add_array('hand_grip', stack_axis=1)

        self.connect(self.daqstream.updated, self.update)
        if self.hand_control:
            self.connect(self.grip, self.robolimb.execute)
        if self.display_output:
            self.connect(self.grip, self.update_text_prediction)

    def update_text_prediction(self, pred):
        self.text_prediction.qitem.setText("Prediction: {}".format(pred))

    def update(self, data):
        data_proc = self.pipeline.process(data)
        pred, proba_max, proba = self.prediction_pipeline.process(data_proc)
        if proba_max >= self.rt.theta_opt_[pred]:
            self.grip.emit(pred)

        # Update Arrays
        self.trial.arrays['data_raw'].stack(data)
        self.trial.arrays['data_proc'].stack(data_proc)
        self.trial.arrays['prediction'].stack(
            str(pred).encode("ascii", "ignore"))
        self.trial.arrays['prediction_proba'].stack(proba)
        if self.hand_control:
            self.trial.arrays['hand_grip'].stack(
                str(self.robolimb.grip).encode("ascii", "ignore"))

        self.timer.increment()

    def finish_trial(self):
        if self.display_output:
            self.text_prediction.hide()
        if self.hand_control:
            self.robolimb.abort_execution()
            self.robolimb.stop_all()
            self.robolimb.open_all()

        self.text_target.hide()
        self.text_relax.show()

        # self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.update)
        if self.hand_control:
            self.disconnect(self.grip, self.robolimb.execute)
        if self.display_output:
            self.disconnect(self.grip, self.text_prediction.qitem.setText)

        self.wait_timer = Timer(TRIAL_INTERVAL)
        self.wait_timer.timeout.connect(self.next_trial)
        self.wait_timer.start()

    def reset(self):
        super(RealTimeControl, self).reset()
        self.text_relax.hide()
        self.text_target.show()
        if self.display_output:
            self.text_prediction.show()

    def finish(self):
        self.daqstream.stop()
        if self.hand_control:
            self.robolimb.stop()
        self.finished.emit()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)


if __name__ == '__main__':
    parser = ArgumentParser()
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument('--train', action='store_true')
    task.add_argument('--test', action='store_true')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--trigno', action='store_true')
    source.add_argument('--myo', action='store_true')
    source.add_argument('--noise', action='store_true')
    robolimb = parser.add_argument('--robolimb', action='store_true')
    display = parser.add_argument('--display', action='store_true')
    args = parser.parse_args()

    cp = ConfigParser()
    cp.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'config.ini'))
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    CHANNELS = list(map(int, (cp.get('hardware', 'channels').split(','))))
    WIN_SIZE = cp.getfloat('processing', 'win_size')
    LOWPASS = cp.getfloat('processing', 'lowpass')
    HIGHPASS = cp.getfloat('processing', 'highpass')
    FILTER_ORDER = cp.getfloat('processing', 'filter_order')
    MOVEMENTS = cp.get('experiment', 'movements').split(',')

    if args.trigno:
        from pytrigno import TrignoEMG
        S_RATE = 2000.
        dev = TrignoEMG(channels=CHANNELS,
                        samples_per_read=int(S_RATE * READ_LENGTH))
    elif args.myo:
        import myo
        from myo.daq import MyoDaqEMG
        CHANNELS = range(8)
        S_RATE = 200.
        myo.init(
            sdk_path=r'C:\Users\nak142\Coding\myo-python\myo-sdk-win-0.9.0')
        dev = MyoDaqEMG(channels=CHANNELS,
                        samples_per_read=int(S_RATE * READ_LENGTH))
    elif args.noise:
        from axopy.daq import NoiseGenerator
        S_RATE = 2000.
        dev = NoiseGenerator(rate=S_RATE, num_channels=8, amplitude=10.0,
                             read_size=int(S_RATE * READ_LENGTH))

    exp = Experiment(daq=dev, subject='test_4', allow_overwrite=True)

    if args.train:
        N_TRIALS = cp.getint('calibration', 'n_trials')
        N_BLOCKS = len(MOVEMENTS)
        TRIAL_LENGTH = cp.getfloat('calibration', 'trial_length')
        TRIAL_INTERVAL = cp.getfloat('calibration', 'trial_interval')
        exp.run(DataCollection())
    elif args.test:
        N_TRIALS = len(MOVEMENTS)
        N_BLOCKS = cp.getint('control', 'n_blocks')
        TRIAL_LENGTH = cp.getfloat('control', 'trial_length')
        TRIAL_INTERVAL = cp.getfloat('control', 'trial_interval')
        exp.run(RealTimeControl(subject=exp.subject,
                                hand_control=args.robolimb,
                                display_output=args.display))
