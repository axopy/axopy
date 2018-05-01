"""Adaptive cursor control mapping example.

This example contains a 2D cursor-to-target task which processes input signals
from a data acquisition device (e.g. from EMG hardware) and adaptively learns a
linear mapping from input magnitude to cursor position via the recursive least
squares (RLS) algorithm.

Once the cursor interface is shown, press the "Enter" key to begin. The target
will move to some location on the screen and the subject should attempt to move
the cursor toward the target. As input data is collected, the recursive least
squares algorithm updates the weights of a linear mapping from input amplitude
to cursor position. Once this training procedure is finished, the target
changes color and the subject can attempt to hit the targets with the mapping
now fixed.
"""

# TODO split this into two tasks (a "training" task and a "practice" task).
# This would involve storing the RLS weights and loading them for the practice
# task. Probably a good idea to write a simple cursor interface class to share
# common code between the two tasks.

import numpy
import random
from scipy.signal import butter

from axopy import pipeline
from axopy.features import mean_absolute_value
from axopy.experiment import Experiment
from axopy import util
from axopy.messaging import transmitter, receiver
from axopy.task import Task, Oscilloscope
from axopy.timing import Counter
from axopy.stream import InputStream
from axopy.gui.canvas import Canvas, Circle, Cross


class RLSMapping(pipeline.Block):
    """Linear mapping of EMG amplitude to position updated by RLS.

    Parameters
    ----------
    m : int
        Number of vectors in the mapping.
    k : int
        Dimensionality of the mapping vectors.
    lam : float
        Forgetting factor.
    """

    def __init__(self, m, k, lam, delta=0.001):
        super(RLSMapping, self).__init__()
        self.m = m
        self.k = k
        self.lam = lam
        self.delta = delta
        self._init()

    @classmethod
    def from_weights(cls, weights):
        """Construct an RLSMapping static weights."""
        obj = cls(1, 1, 1)
        obj.weights = weights
        return obj

    def _init(self):
        self.w = numpy.zeros((self.k, self.m))
        self.P = numpy.eye(self.m) / self.delta

    def process(self, data):
        """Just applies the current weights to the input."""
        self.y = data
        self.xhat = self.y.dot(self.w.T)
        return self.xhat

    def update(self, x):
        """Update the weights with the teaching signal."""
        z = self.P.dot(self.y.T)
        g = z / (self.lam + self.y.dot(z))
        e = x - self.xhat
        self.w = self.w + numpy.outer(e, g)
        self.P = (self.P - numpy.outer(g, z)) / self.lam


class CursorFollowing(Task):

    def __init__(self, pipeline):
        super(CursorFollowing, self).__init__()
        self.pipeline = pipeline

        trials = []
        for training in [True, False]:
            for i in range(4):
                p = 0.8
                for x, y in [(p, 0), (0, p), (0, 0), (-p, 0), (0, -p)]:
                    trials.append({
                        'pos': numpy.array([x, y]),
                        'training': training
                    })
            if training:
                random.shuffle(trials)
        design = [trials]
        self.design(design)

    def prepare_view(self, view):
        self.canvas = Canvas()
        self.cursor = Circle(0.05, color='#aa1212')
        self.target = Circle(0.1, color='#32b124')
        self.canvas.add_item(self.target)
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(Cross())
        view.set_view(self.canvas)

    def prepare_input_stream(self, input_stream):
        self.input_stream = input_stream
        self.input_stream.start()

        self.timer = Counter(50)
        self.timer.timeout.connect(self.finish_trial)

    def run_trial(self, trial):
        if not trial['training']:
            self.target.set_color('#3224b1')
        pos = trial['pos']
        self._reset()
        self.target.setPos(pos[0], pos[1])
        self.target.setVisible(True)
        self.pipeline.clear()
        self.connect(self.input_stream.updated, self.update)

    def update(self, data):
        xhat = self.pipeline.process(data)
        self.cursor.setPos(xhat[0], xhat[1])

        if self.trial['training']:
            self.pipeline.named_blocks['RLSMapping'].update(self.trial['pos'])

        if self.cursor.collidesWithItem(self.target):
            self.finish_trial()

        self.timer.increment()

    def finish_trial(self):
        self.disconnect(self.input_stream.updated, self.update)
        self._reset()
        self.next_trial()

    def _reset(self):
        self.cursor.setPos(0, 0)
        self.timer.reset()
        self.target.setVisible(False)

    def finish(self):
        self.input_stream.kill()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)


if __name__ == '__main__':
    # from pytrigno import TrignoEMG
    # dev = TrignoEMG((0, 3), 200, host='192.168.1.114', units='normalized')
    from axopy.stream import EmulatedDaq
    dev = EmulatedDaq(rate=2000, num_channels=4, read_size=200)

    b, a = butter(4, (10/2000./2., 450/2000./2.), 'bandpass')
    preproc_pipeline = pipeline.Pipeline([
        pipeline.Windower(400),
        pipeline.Centerer(),
        pipeline.Filter(b, a=a, overlap=200),
    ])
    main_pipeline = pipeline.Pipeline([
        preproc_pipeline,
        pipeline.Callable(mean_absolute_value),
        RLSMapping(4, 2, 0.99)
    ])

    Experiment(daq=dev, subject='test').run(
        Oscilloscope(preproc_pipeline),
        CursorFollowing(main_pipeline)
    )
