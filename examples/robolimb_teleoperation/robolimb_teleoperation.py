"""
TODO Docstring
"""

import os
import joblib
import numpy as np
import time

from argparse import ArgumentParser
from configparser import ConfigParser

from axopy.experiment import Experiment
from axopy.task import Task
from axopy import util
from axopy.timing import Counter, Timer
from axopy.gui.canvas import Canvas, Text
from axopy.pipeline import (Callable, Windower, Pipeline, Ensure2D)
from axopy.features import mean_value

from robolimb import RoboLimbCAN as RoboLimb
from cyberglove import CyberGlove


class _BaseTask(Task):
    """Base experimental task.

    TODO
    """

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()

    def key_press(self, key):
        super(_BaseTask, self).key_press(key)
        if key == util.key_escape:
            self.finish()

    def finish(self):
        self.daqstream.stop()
        self.finished.emit()


class Calibration(_BaseTask):
    """Docstring todo
    """

    def __init__(self):
        super(Calibration, self).__init__()
        self.pipeline = self.make_pipeline()

    def make_pipeline(self):
        pipeline = Pipeline([
            #Windower(int(GLOVE_S_RATE * WIN_SIZE)),
            Ensure2D(orientation='row'),
            Callable(mean_value),
            Callable(lambda x: np.dot(x, GLOVE_FINGER_MAP)),
            Ensure2D(orientation='col')
        ])

        return pipeline

    def prepare_daq(self, daqstream):
        super(Calibration, self).prepare_daq(daqstream)

        # Set trial length
        self.timer = Counter(
            int(TRIAL_LENGTH / READ_LENGTH))  # daq read cycles
        self.timer.timeout.connect(self.finish_trial)

    def prepare_design(self, design):
        # There is one block, each movement is one trial
        block = design.add_block()
        for movement in MOVEMENTS:
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
        trial.add_array('glove_proc', stack_axis=1)

        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        data_proc = self.pipeline.process(data)
        # Update Arrays
        self.trial.arrays['glove_proc'].stack(data_proc)

        self.timer.increment()

    def finish_trial(self):
        # self.pic.hide()
        self.text.qitem.setText("{}".format('relax'))
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.update)

        self.wait_timer = Timer(TRIAL_INTERVAL)
        self.wait_timer.timeout.connect(self.next_trial)
        self.wait_timer.start()

    def reset(self):
        self.timer.reset()


class RealTimeControl(_BaseTask):
    """Real-time robolimb teleoperation.

    TODO
    """

    def __init__(self, subject):
        super(RealTimeControl, self).__init__()
        self.advance_block_key = None
        self.subject = subject

        self.load_calibration_data()
        self.pipeline = self.make_pipeline()

        self.hand = RoboLimb()
        self.hand.start()
        self.hand.open_all()
        self.cur_pos = np.ones((N_DOF_HAND,))

    def load_calibration_data(self):
        root_models = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'data', self.subject, 'models')
        self.cal_min = joblib.load(os.path.join(root_models, 'cal_min'))
        self.cal_max = joblib.load(os.path.join(root_models, 'cal_max'))

    def make_pipeline(self):
        """Glove pipeline. """
        pipeline = Pipeline([
            Ensure2D(orientation='row'),
            Callable(mean_value),
            Callable(lambda x: np.dot(x, GLOVE_FINGER_MAP)),
            Callable(lambda x:
                     (x - self.cal_min) / (self.cal_max - self.cal_min)),
            Callable(np.clip, func_kwargs={'a_min': 0., 'a_max': 1.})
        ])
        return pipeline

    def prepare_design(self, design):
        # Single free run
        block = design.add_block()
        block.add_trial()

    def prepare_graphics(self, container):
        self.canvas = Canvas()
        container.set_widget(self.canvas)

    def run_trial(self, trial):
        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        cur_pos = self.pipeline.process(data)
        prev_pos = self.cur_pos.copy()
        for i in range(N_DOF_HAND):
            if (cur_pos[i] - prev_pos[i] > EPS) or (cur_pos[i] > 1. - EPS_LIM):
                if self.hand.finger_status[i] not in ['closing', 'stalled close']:
                    self.hand.close_finger(i + 1, velocity=FINGER_SPEED)
            elif (cur_pos[i] - prev_pos[i] < -EPS) or (cur_pos[i] < EPS_LIM):
                if self.hand.finger_status[i] not in ['opening', 'stalled open']:
                    self.hand.open_finger(i + 1, velocity=FINGER_SPEED)
            else:
                self.hand.stop_finger(i + 1)

        self.cur_pos = cur_pos

    def finish(self):
        self.disconnect(self.daqstream.updated, self.update)
        self.daqstream.stop()
        self.hand.stop_all()
        self.hand.open_all()
        time.sleep(2)
        self.hand.close_finger(1)
        self.hand.stop()
        self.finished.emit()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)


if __name__ == '__main__':
    subject = 'test'

    parser = ArgumentParser()
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument('--calibrate', action='store_true')
    task.add_argument('--run', action='store_true')
    args = parser.parse_args()

    cp = ConfigParser()
    cp.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'config.ini'))
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    GLOVE_PORT = cp.get('hardware', 'glove_port')
    N_DOF_GLOVE = cp.getint('hardware', 'n_dof_glove')
    N_DOF_HAND = cp.getint('hardware', 'n_dof_hand')
    MOVEMENTS = cp.get('calibration', 'movements').split(',')
    TRIAL_LENGTH = cp.getfloat('calibration', 'trial_length')
    TRIAL_INTERVAL = cp.getfloat('calibration', 'trial_interval')
    FINGER_SPEED = cp.getint('control', 'finger_speed')
    EPS = cp.getfloat('control', 'epsilon')
    EPS_LIM = cp.getfloat('control', 'epsilon_limit')

    GLOVE_S_RATE = 40.
    GLOVE_FINGER_MAP = np.loadtxt(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'map.csv'),
        delimiter=',')

    cal_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'data', subject, 'glove_calibration.cal')
    dev = CyberGlove(n_df=18, s_port=GLOVE_PORT, cal_path=cal_path,
                     samples_per_read=int(GLOVE_S_RATE * READ_LENGTH))
    exp = Experiment(daq=dev, subject=subject, allow_overwrite=True)

    if args.calibrate:
        exp.run(Calibration())
    elif args.run:
        exp.run(RealTimeControl(subject=subject))
