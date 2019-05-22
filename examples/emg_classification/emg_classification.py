"""
Collect training data. Show videos with 6 classes (5 movements + rest).
For now just show label.
TODO:
* training: sound before trial start
* training and control: pics instead
* control: pipeline spit out both pred and proba (in parallel)

"""
import os
import joblib
import time
import numpy as np

from argparse import ArgumentParser
from configparser import ConfigParser
from scipy.signal import butter

from PyQt5.QtCore import QThread
from can.interfaces.pcan import PCANBasic as pcan

from axopy.experiment import Experiment
from axopy.task import Task
from axopy import util
from axopy.timing import Counter, Timer
from axopy.gui.canvas import Canvas, Text
from axopy.pipeline import (Callable, Windower, Filter, Pipeline, FeatureExtractor,
                            Ensure2D, Estimator, Transformer)
from axopy.features import waveform_length, logvar

from robolimb import RoboLimbCAN


class RoboLimbGrip(RoboLimbCAN):
    def __init__(self,
                 def_vel=297,
                 read_rate=0.02,
                 channel=pcan.PCAN_USBBUS1,
                 b_rate=pcan.PCAN_BAUD_1M,
                 hw_type=pcan.PCAN_TYPE_ISA,
                 io_port=0x3BC,
                 interrupt=3):
        super().__init__(
            def_vel,
            read_rate,
            channel,
            b_rate,
            hw_type,
            io_port,
            interrupt)

        self.grip = None
        self.executing = False
        self.grip_queued = None

    def execute(self, grip, force):
        """Performs grip at maximum velocity."""
        velocity = 297
        if (force is False and self.executing is True) or (self.grip == grip):
            pass
        else:
            self.executing = True
            if grip == 'open':
                self.open_fingers(velocity=velocity)
                time.sleep(1)
                self.grip = 'open'
            elif grip == 'power':
                # Preparation
                [self.open_finger(i, velocity=velocity) for i in range(1, 6)]
                time.sleep(0.2)
                self.close_finger(6, velocity=velocity)
                time.sleep(1.3)
                # Execution
                self.stop_all()
                self.close_fingers(velocity=velocity, force=True)
                time.sleep(1)
                self.grip = 'power'
            elif grip == 'lateral':
                # Preparation
                [self.open_finger(i, velocity=velocity) for i in range(1, 4)]
                time.sleep(0.2)
                self.open_finger(6, velocity=velocity, force=True)
                time.sleep(0.1)
                [self.stop_finger(i) for i in range(2, 4)]
                [self.close_finger(i, velocity=velocity) for i in range(2, 6)]
                time.sleep(1.2)
                # Execution
                self.stop_all()
                self.close_finger(1, velocity=velocity, force=True)
                time.sleep(1)
                self.grip = 'lateral'
            elif grip == 'tripod':
                # Preparation
                [self.open_finger(i, velocity=velocity) for i in range(1, 4)]
                time.sleep(0.1)
                [self.stop_finger(i) for i in range(1, 4)]
                [self.close_finger(i, velocity=velocity) for i in range(4, 7)]
                time.sleep(1.4)
                # Execution
                self.stop_all()
                [self.close_finger(i, velocity=velocity, force=True)
                 for i in range(1, 4)]
                time.sleep(1)
                self.grip = 'tripod'
            elif grip == 'pointer':
                # Preparation
                [self.open_finger(i, velocity=velocity) for i in range(1, 3)]
                time.sleep(0.1)
                self.open_finger(6, velocity=velocity)
                time.sleep(1.4)
                # Execution
                self.stop_all()
                [self.close_finger(i, velocity=velocity, force=True)
                 for i in [1, 3, 4, 5]]
                time.sleep(1)
                self.grip = 'pointer'

            self.executing = False


class RoboLimbControl(QThread):
    def __init__(self, robolimb):
        super(RoboLimbControl, self).__init__()
        self.running = True
        self.robolimb = robolimb
        self.robolimb.start()

    def run(self):
        while self.running:
            self.robolimb.execute(self.robolimb.grip_queued, force=False)
            time.sleep(0.001)

    def stop(self):
        self.running = False
        self.exit()


class WaveformLength(object):
    def __init__(self):
        pass

    def compute(x):
        return waveform_length(x)


class LogVar(object):
    def __init__(self):
        pass

    def compute(x):
        return logvar(x)


class _BaseTask(Task):
    def __init__(self):
        super(_BaseTask, self).__init__()

        self.pipeline = self.make_pipeline()

    def make_pipeline(self):
        # Multiple feature extraction could also be implemented using a parallel
        # pipeline and a block that joins multiple outputs
        b, a = butter(4, (10/2000./2., 900/2000./2.), 'bandpass')
        pipeline = Pipeline([
            Windower(int(S_RATE * WIN_SIZE)),
            Filter(b, a=a,
                   overlap=(int(S_RATE * WIN_SIZE) -
                            int(S_RATE * READ_LENGTH))),
            FeatureExtractor([('wl', WaveformLength), ('logvar', LogVar)]),
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


class DataCollection(_BaseTask):
    def __init__(self):
        super(DataCollection, self).__init__()
        # self.advance_block_key = None  # No wait between blocks

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
        self.canvas.add_item(self.text)
        container.set_widget(self.canvas)

    def prepare_storage(self, storage):  # TODO
        self.writer = storage.create_task('calibration')

    def run_trial(self, trial):
        self.reset()
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
        self.text.qitem.setText("{}".format('relax'))
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.update)

        self.wait_timer = Timer(TRIAL_INTERVAL)
        self.wait_timer.timeout.connect(self.next_trial)
        self.wait_timer.start()


class RealTimeControl(_BaseTask):
    def __init__(self, subject):
        super(RealTimeControl, self).__init__()
        self.subject = subject

        self.load_models()
        self.prediction_pipeline = self.make_prediction_pipeline()
        self.prediction_proba_pipeline = self.make_prediction_proba_pipeline()

        self.robolimb = RoboLimbGrip()
        self.robolimb.start()
        self.robolimb.open_all()

        self.robolimb_control = RoboLimbControl(self.robolimb)
        self.robolimb_control.start()

    def load_models(self):
        root_models = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'data', self.subject, 'models')
        self.clf = joblib.load(os.path.join(root_models, 'classifier'))
        self.ssc = joblib.load(os.path.join(root_models, 'input_scaler'))
        self.le = joblib.load(os.path.join(root_models, 'output_encoder'))
        self.rt = joblib.load(os.path.join(root_models, 'roc_thresholds'))

    def make_prediction_pipeline(self):
        pipeline = Pipeline([
            Callable(lambda x: np.transpose(x)),  # Transpose
            Transformer(self.ssc),
            Estimator(self.clf),
            Transformer(self.le, inverse=True),
            Callable(lambda x: x[0])
        ])

        return pipeline

    def make_prediction_proba_pipeline(self):
        pipeline = Pipeline([
            Callable(lambda x: np.transpose(x)),  # Transpose
            Transformer(self.ssc),
            Estimator(self.clf, return_proba=True),
            Callable(lambda x: np.max(x))
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

        self.text_prediction = Text(text='', color='red')
        self.text_prediction.pos = (-0.35, 0.0)

        self.text_relax = Text(text='', color='black')
        self.text_relax.qitem.setText('relax')
        self.text_relax.pos = (-0.1, 0.1)
        self.text_relax.hide()

        self.canvas.add_item(self.text_target)
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

        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        data_proc = self.pipeline.process(data)
        pred = self.prediction_pipeline.process(data_proc)
        proba = self.prediction_proba_pipeline(data_proc)

        self.text_prediction.pos = (-0.35, 0.0)
        self.text_prediction.qitem.setText(
            "Prediction: {}, proba {}".format(pred, proba))

        if proba >= self.rt.theta_opt_[pred]:
            self.robolimb.grip_queued = pred

        # Update Arrays
        self.trial.arrays['data_raw'].stack(data)
        self.trial.arrays['data_proc'].stack(data_proc)
        self.trial.arrays['prediction'].stack(str(pred).encode("ascii",
                                                               "ignore"))

        self.timer.increment()

    def finish_trial(self):
        self.text_prediction.hide()
        self.text_target.hide()
        self.text_relax.show()

        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.update)

        self.robolimb.grip_queued = 'open'

        self.wait_timer = Timer(TRIAL_INTERVAL)
        self.wait_timer.timeout.connect(self.next_trial)
        self.wait_timer.start()

    def reset(self):
        super(RealTimeControl, self).reset()
        self.text_relax.hide()
        self.text_target.show()
        self.text_prediction.show()

    def finish(self):
        self.daqstream.stop()
        self.robolimb.open_all()
        time.sleep(1.5)
        self.robolimb.close_finger(1)
        time.sleep(1)
        self.robolimb.stop()
        self.robolimb_control.stop()
        self.finished.emit()


if __name__ == '__main__':
    parser = ArgumentParser()
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument('--train', action='store_true')
    task.add_argument('--test', action='store_true')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--trigno', action='store_true')
    source.add_argument('--noise', action='store_true')
    args = parser.parse_args()

    cp = ConfigParser()
    cp.read('config.ini')
    S_RATE = cp.getfloat('hardware', 's_rate')
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    WIN_SIZE = cp.getfloat('processing', 'win_size')
    MOVEMENTS = cp.get('experiment', 'movements').split(',')

    if args.trigno is True:
        from pytrigno import TrignoEMG
        dev = TrignoEMG(channels=range(9),
                        samples_per_read=int(S_RATE * READ_LENGTH))
    elif args.noise is True:
        from axopy.daq import NoiseGenerator
        dev = NoiseGenerator(rate=S_RATE, num_channels=9, amplitude=1.0,
                             read_size=int(S_RATE * READ_LENGTH))

    exp = Experiment(daq=dev, subject='test', allow_overwrite=True)

    if args.train is True:
        N_TRIALS = cp.getint('calibration', 'n_trials')
        N_BLOCKS = len(MOVEMENTS)
        TRIAL_LENGTH = cp.getfloat('calibration', 'trial_length')
        TRIAL_INTERVAL = cp.getfloat('calibration', 'trial_interval')

        exp.run(DataCollection())
    elif args.test is True:
        N_TRIALS = len(MOVEMENTS)
        N_BLOCKS = cp.getint('control', 'n_blocks')
        TRIAL_LENGTH = cp.getfloat('control', 'trial_length')
        TRIAL_INTERVAL = cp.getfloat('control', 'trial_interval')

        exp.run(RealTimeControl(subject=exp.subject))
