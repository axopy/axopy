"""
Two daqstreams
==============

This example demonstrates the use of multiple daq devices. It reads from two
``daqstream`` objects with different sampling rates. The ``read_size`` for
the devices is set such that it takes the same amount of time to perform a read
operation from them. The data are then combined and displayed on a Oscilloscope.

The raw and processed data are stored for both devices so that the user can
check that they have appropriate sizes.
"""
import numpy as np
from scipy.signal import butter

from axopy.experiment import Experiment
from axopy.task import Task
from axopy import util
from axopy.gui.graph import SignalWidget
from axopy.timing import Counter, Timer
from axopy.pipeline import Windower, Filter, Callable, Pipeline
from axopy.design import Array
from axopy.daq import DaqStream


class MyTask(Task):
    def __init__(self):
        super(MyTask, self).__init__()
        self.make_display_pipeline()

    def prepare_design(self, design):
        block = design.add_block()
        block.add_trial()
        block.shuffle()

    def prepare_graphics(self, container):
        self.scope = SignalWidget()
        container.set_widget(self.scope)

    def prepare_storage(self, storage):  # TODO
        self.writer = storage.create_task('sync_daqs')

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        for daqstream_ in self.daqstream:
            daqstream_.start()

        # The following list of booleans is used to keep track of when
        # all daqstreams have been updated so as to increment the timer
        self.daqstream_updated = len(self.daqstream) * [False]

        self.timer = Counter(50)
        self.timer.timeout.connect(self.finish_trial)

    def make_pipeline(self, win_size, read_size):
        b, a = butter(4, (10/2000./2., 900/2000./2.), 'bandpass')
        pipeline = Pipeline([
            Windower(win_size),
            Filter(b, a=a, overlap=(win_size - read_size)),
            Callable(lambda x: x[:, 0].reshape(-1, 1))  # Downsampling
        ])

        return pipeline

    def make_display_pipeline(self):
        self.display_pipeline = Pipeline([
            Windower(30)
        ])

    def run_trial(self, trial):
        self.reset()
        trial.add_array('dev_1_raw', stack_axis=1)
        trial.add_array('dev_1_processed', stack_axis=1)
        trial.add_array('dev_2_raw', stack_axis=1)
        trial.add_array('dev_2_processed', stack_axis=1)

        # Each device has its own pipeline for data processing
        self.pipeline_dev_1 = self.make_pipeline(win_size=250, read_size=200)
        self.pipeline_dev_2 = self.make_pipeline(win_size=250, read_size=100)

        self.connect(self.daqstream[0].updated, self.update_dev_1)
        self.connect(self.daqstream[1].updated, self.update_dev_2)

    def reset(self):
        self.timer.reset()
        # Clear data from window used for Oscilloscope.
        self.display_pipeline.clear()
        self.pooled_data = 2 * [None]

    def update_dev_1(self, data):
        data_proc = self.pipeline_dev_1.process(data)
        self.pooled_data[0] = data_proc

        self.trial.arrays['dev_1_raw'].stack(data)
        self.trial.arrays['dev_1_processed'].stack(data_proc)

        self.daqstream_updated[0] = True
        self.check_all_updated()

    def update_dev_2(self, data):
        data_proc = self.pipeline_dev_2.process(data)
        self.pooled_data[1] = data_proc

        self.trial.arrays['dev_2_raw'].stack(data)
        self.trial.arrays['dev_2_processed'].stack(data_proc)

        self.daqstream_updated[1] = True
        self.check_all_updated()

    def check_all_updated(self):
        """Checks if all daqstreams have been updated."""
        if all(self.daqstream_updated):
            self.update_scope()
            self.finish_cycle()

    def update_scope(self):
        pooled_data_ar = np.concatenate((
            self.pooled_data[0], self.pooled_data[1]))
        data_display = self.display_pipeline.process(pooled_data_ar)
        self.scope.plot(data_display)

    def finish_cycle(self):
        """Resets ``daqstream_updated`` and ``pooled_data``."""
        self.daqstream_updated = len(self.daqstream) * [False]
        self.pooled_data = len(self.daqstream) * [None]
        self.timer.increment()

    def finish_trial(self):
        self.writer.write(self.trial)
        self.disconnect(self.daqstream[0].updated, self.update_dev_1)
        self.disconnect(self.daqstream[1].updated, self.update_dev_2)

        self.next_trial()

    def key_press(self, key):
        super(MyTask, self).key_press(key)
        if key == util.key_escape:
            self.finish()

    def finish(self):
        for daqstream_ in self.daqstream:
            daqstream_.stop()
        self.finished.emit()


if __name__ == '__main__':
    # from axopy.daq import NoiseGenerator
    # dev_1 = NoiseGenerator(
    #     rate=2000,
    #     num_channels=4,
    #     amplitude=1.0,
    #     read_size=200)
    # dev_2 = NoiseGenerator(
    #     rate=1000,
    #     num_channels=2,
    #     amplitude=1.0,
    #     read_size=100)
    from pytrigno import TrignoEMG
    from cyberglove import CyberGlove

    dev_1 = TrignoEMG(channels=[0,1], samples_per_read=200)

    dev_2 = CyberGlove(18, 'COM3', samples_per_read=4,
                     cal_path=r"C:\Users\nak142\tmp\glove.cal")




    exp = Experiment(daq=[dev_1, dev_2],
                     subject='test_',
                     allow_overwrite=True)
    exp.run(MyTask())
