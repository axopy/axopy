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


def cardinal_out_and_back_trajectories(samples):
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


class CursorFollowing(Task):

    def __init__(self, trajectories, reps=1):
        # build up an experiment structure
        # each block consists of every trajectory shuffled randomly
        blocks = []
        for i in range(reps):
            block = []
            for traj in trajectories:
                trial = dict(trajectory=traj)
                block.append(trial)
            random.shuffle(block)
            blocks.append(block)
        self.iter = TaskIter(blocks)

        exp_dir = init_task_storage(self.__class__.__name__)
        cols = ['block', 'trial', 'emg_file', 'cursor_file']
        self.trials_storage = TableWriter('trials', cols, data_path=exp_dir)
        self.emg_storage = ArrayWriter('emg', data_path=exp_dir)
        self.cursor_storage = ArrayWriter('paths', data_path=exp_dir)

    def prepare(self):
        self.ui = Canvas(bg_color=bg_color)

        self.cursor = Circle(cursor_size, color=cursor_color)
        self.ui.add_item(self.cursor)

        self.fixcross = Cross()
        self.ui.add_item(self.fixcross)

        self.device_stream.update.connect(self.update)
        self.finish_trial.connect(self.ui.clear)

    def run_trial(self, trial):
        self.current_trajectory = trial.trajectory
        self.cursor.move_to(0, 0)

        self.device_stream.start()

    def update(self, data):
        pos = next(self.current_trajectory)
        self.cursor.move_to(*(100*pos))

        self.emg_storage.add(data)
        self.cursor_storage.add(numpy.atleast_2d(pos).T)

        self.experiment.keyboard.check()

        self.input_device.stop()
        self.clear()

        tup = (self.experiment.subject, self.block.id, self.trial.id)
        cfp = self.cursor_storage.write(*tup)
        efp = self.emg_storage.write(*tup)
        self.experiment.data.add([self.block.id, self.trial.id, cfp, efp])

        self.experiment.clock.wait(1000)

    def finish_trial(self):
        self.input_device.stop()
        self.clear()

        tup = (self.experiment.subject, self.block.id, self.trial.id)
        cfp = self.cursor_storage.write(*tup)
        efp = self.emg_storage.write(*tup)
        self.experiment.data.add([self.block.id, self.trial.id, cfp, efp])

    def clear(self):
        """Draw only the static elements of the interface."""
        self.area_rect.present(clear=True)
        self.fixcross.present(clear=False)

    @staticmethod
    def load_data(subject):
        """Yields (emg_data, cursor_position) pairs from a subject's data."""
        emg_dir = os.path.join(data_root, 'CursorFollowing', 'emg')
        emg_files = sorted(os.listdir(emg_dir))

        cursor_dir = os.path.join('data', 'CursorFollowing', 'paths')
        cursor_files = sorted(os.listdir(cursor_dir))

        for efn, cfn in zip(emg_files, cursor_files):
            emg_data = read_hdf5(os.path.join(emg_dir, efn))
            cursor_data = read_hdf5(os.path.join(cursor_dir, cfn))
            seg_length = int(emg_data.shape[1] / cursor_data.shape[1])
            for i, x in enumerate(copper.segment(emg_data, seg_length)):
                yield x, cursor_data[:, i]

    @staticmethod
    def load_training_dataset(subject, emg_pipeline):
        emg_data = ArrayBuffer()
        cursor_data = ArrayBuffer()
        for emg, cursor in CursorFollowing.load_data(subject):
            emg_proc = emg_pipeline.process(emg)
            emg_data.add(emg_proc)
            cursor_data.add(cursor)

        return emg_data.data, cursor_data.data
