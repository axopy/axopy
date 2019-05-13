"""
Simple Robolimb keyboard control
================================

When key ``c`` is pressed, close all fingers. When key ``o`` is pressed open
all  fingers.
"""

import time
import numpy as np

from axopy import pipeline
from axopy.daq import Keyboard
from axopy.experiment import Experiment
from axopy.timing import Counter
from axopy.task import Task
from axopy.timing import Counter
from axopy import util

from robolimb import RoboLimbCAN as RoboLimb

class RLTask(Task):
    def __init__(self, hand):
        super(RLTask, self).__init__()
        self.hand = hand

        self.init_hand()

    def init_hand(self):
        self.hand.start()
        self.hand.open_all()

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.connect(self.daqstream.updated, self.update)

    def run(self):
        self.daqstream.start()

    def update(self, data):
        if data[0] == 1:
            self.hand.close_fingers()
        elif data[1] == 1:
            self.hand.open_fingers()

    def key_press(self, key):
        if key == util.key_return:
            self.finish()

    def finish(self):
        self.daqstream.stop()

        self.hand.open_all()
        time.sleep(1)
        self.hand.close_finger(1)
        self.hand.stop()

        self.finished.emit()

if __name__ == "__main__":
    dev = Keyboard(rate=20, keys=list('co'))
    hand = RoboLimb()
    Experiment(daq=dev, subject='test').run(RLTask(hand))
