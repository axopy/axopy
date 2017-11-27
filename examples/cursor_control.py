"""Cursor control example.

This example experiment implements a continuous myoelectric control of a cursor
in two dimensions via a scikit-learn regression model trained on simple
amplitude-based features. There are two configurations:

    1. ``'ridge'``: Use a ridge regression model.
    2. ``'forest'``: Use a random forest regressor model.

The tasks are the same for both configurations, with the exception of the model
used in the ``CursorControl`` task:

    1. ``Oscilloscope``: shows a simple oscilloscope view of the raw EMG data.
        This task is built in to AxoPy.
    2. ``CursorFollowing``: displays a cursor automatically moving around the
       screen while the subject attempts to "follow" it with the wrist. Raw EMG
       data recorded during each trial is recorded as well as the cursor
       position.
    3. ``Preprocessing``: reads in the data from CursorFollowing task and
       computes features from the EMG signals. The features and cursor position
       are all placed into a large table for ease of analysis using
       scikit-learn.
    4. ``CursorControl``: reads in the cursor position and EMG feature pairs to
       train a scikit-learn model (depending on the coniguration), then uses
       the model to produce output cursor position given EMG data. The subject
       attempts to hit randomly presented targets around the screen. Cursor
       trajectories and raw EMG data are recorded.
"""

import random
import os
import numpy
import copper
from axopy import Task, TaskIter
from axopy.gui.canvas import Canvas, Circle, Cross
from axopy.storage import (init_task_storage, ArrayWriter, ArrayBuffer,
                           TableWriter, read_hdf5)

# global experiment settings
cursor_color = (10, 100, 120)
cursor_size = 0.05
target_color = (150, 10, 10)
target_size = 0.1
bg_color = (30, 30, 30)

sample_rate = 2000
samples_per_update = 200

data_root = 'data'


def create_design(attrs, attr_name='attr', num_blocks=1, shuffle=True):
    """Generate a task design from per-trial attributes.

    Takes in a list of attributes, where each trial of a block contains a trial
    with each attribute.
    """
    design = []
    for iblock in range(num_blocks):
        block = []
        for itrial, attr in enumerate(attrs):
            block.append({
                'block': iblock,
                'trial': itrial,
                attr_name: attr
            })
        if shuffle:
            block.shuffle()
        design.append(block)
    return design


def cardinal_out_and_back_trajectories(nsamples):
    """Generate out-and-back trajectories with sinusoid velocity profiles.

    Trajectories for each of the four cardinal directions are generated: right,
    up, left, then down.
    """
    t = numpy.linspace(0, numpy.pi, samples)
    dome = numpy.sin(t)[:, None]
    trajectories = []
    for c1, c2 in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        trajectories.append(numpy.hstack([c1*dome, c2*dome]))
    return trajectories


def setup_cursor_view(cursor_size=5, target_size=10, cursor_color='#aa1212',
                      target_color='#32b124'):
    """Initialize a basic cursor/target canvas.

    Returns
    -------
    cursor : Circle
        The cursor.
    target : Circle
        The target.
    canvas : Canvas
        The canvas. The cursor and target are added for you.
    """
    canvas = Canvas()
    cursor = Circle(cursor_size, color=cursor_color)
    target = Circle(target_size, color=target_color)

    canvas.add_item(target)
    canvas.add_item(cursor)
    canvas.add_item(Cross())

    return cursor, target, canvas


class CursorFollowing(Task):
    """Task in which the subject imagines following a moving cursor.

    Flow:
        - block starts
            - trial starts
                - increment cursor position
                - log raw EMG data and cursor position
                - if last position, finish trial
            - trial finishes
                - save data
                - start a timer to initiate the next trial
         - block finishes
            - wait for key press to continue
    """

    def __init__(self, blocks=1, name='cursor_following',
                 inter_trial_timeout=3):
        self.name = name
        self.design(create_design(cardinal_out_and_back_trajectories(20)))

    def prepare_view(self, container):
        self.cursor, self.target, self.canvas = \
            setup_cursor_view(**self.cursor_view_params)
        container.set_view(self.canvas)

    def prepare_input_stream(self, input_stream):
        input_stream.update.connect(self.update)

    def prepare_storage(self, storage):
        self.writer = storage.create_task(self.name,
                                          ['block', 'trial', 'direction'],
                                          array_names=['emg', 'cursor'])

    def run_trial(self, trial):
        # TODO: canvas object show/hide
        self.cursor.show()
        self.cursor.move_to(0, 0)

        self.input_stream.start()

        self.current_trial = trial
        self.pos_iter = iter(trial['cursor'])
        self.update_pos()

    def update_pos(self):
        try:
            self.cursor_pos = next(self.pos_iter)
        except StopIteration:
            self.finish_trial()

    def update(self, data):
        # move the cursor in the canvas
        self.cursor.move_to(*(100*self.cursor_pos))

        # save the EMG data and the cursor position
        self.writer.arrays['emg'].stack(data)
        self.writer.arrays['cursor'].stack(numpy.atleast_2d(pos).T)

        # update position at the end in case it's the last of this trial
        self.update_pos()

    def finish_trial(self):
        self.input_device.stop()
        self.clear()

        self.writer.write([
            self.current_trial['block'],
            self.current_trial['trial'],
            self.current_trial['direction']
        ])

        # start timer to wait for next trial
        # TODO: implement
        OneShotTimer.delayed_call(self.next_trial,
                                  self.inter_trial_timeout)

    def key_press(self, key):
        if self.awaiting_next_block and key == util.key_return:
            self.awaiting_next_block = False

    def clear(self):
        self.cursor.hide()


class Preprocessing(Task):

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def prepare_view(self, view):
        # TODO set up a pyqtgraph plot

    def prepare_storage(self, storage):
        # TODO set up some variables for later
        pass

    def processs(self):
        # TODO iterate over input data, run through pipeline, write output
        pass

    def key_press(self, key):
        if key == util.key_return:
            self.process()


class CursorControl(Task):

    def __init__(self, model_cls=None, interface_params=None):
        self.model_cls = model_cls
        self.interface_params = interface_params

    def prepare_view(self, view):
        self.cursor_view = CursorView(**self.interface_params)
        view.set(self.cursor_view)

    def prepare_storage(self, storage):



if __name__ == '__main__':
    design = {
        'ridge': [
            Oscilloscope(),
            CursorFollowing(),
            Preprocessing(),
            CursorControl(model_cls=Ridge)
        ],
        'forest': [
            Oscilloscope(),
            CursorFollowing(),
            Preprocessing(),
            CursorControl(model_cls=RandomForestRegressor)
        ]
    }

    exp = Experiment(design)
