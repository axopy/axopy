import copper
import exgfeatures as exg
import numpy
import random
from scipy.signal import butter

from axopy.experiment import Experiment
from axopy import util
from axopy.messaging import transmitter, receiver
from axopy.task import Task, Oscilloscope, SubjectSelection
from axopy.timing import IncrementalTimer
from axopy.stream import InputStream
from axopy.gui.canvas import Canvas, Circle, Cross


class RLSMapping(copper.PipelineBlock):
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
        trials = []
        for training in [True, False]:
            for i in range(4):
                p = 80
                for x, y in [(p, 0), (0, p), (0, 0), (-p, 0), (0, -p)]:
                    trials.append(
                        {
                            'pos': numpy.array([x, y]),
                            'training': training
                        }
                    )
            if training:
                random.shuffle(trials)
        design = [trials]

        self.pipeline = pipeline

        self.design(design)

    def prepare_view(self, view):
        self.canvas = Canvas()
        self.cursor = Circle(5, color='#aa1212')
        self.target = Circle(10, color='#32b124')
        self.canvas.add_item(self.target)
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(Cross())
        view.set_view(self.canvas)

    def prepare_input_stream(self, input_stream):
        self.input_stream = input_stream
        self.input_stream.updated.connect(self.update)
        self.input_stream.finished.connect(self.stopped)

        self.timer = IncrementalTimer(50)
        self.timer.timeout.connect(self.finish_trial)
        self.update.connect(self.timer.increment)

    def run_trial(self, trial):
        self.current_trial = trial
        if not trial['training']:
            self.target.set_color('#3224b1')
        pos = trial['pos']
        self._reset()
        self.target.move_to(pos[0], pos[1])
        self.target.setVisible(True)
        self.input_stream.start()
        self.pipeline.clear()

    @transmitter()
    def update(self, data):
        xhat = self.pipeline.process(data)
        self.cursor.move_to(xhat[0], xhat[1])

        if self.current_trial['training']:
            self.pipeline.named_blocks['RLSMapping'].update(
                self.current_trial['pos'])

        if self.cursor.collidesWithItem(self.target):
            self.finish_trial()

        return

    @receiver
    def finish_trial(self):
        self._reset()
        self.input_stream.kill(wait=False)

    @receiver
    def stopped(self):
        self.next_trial()

    def _reset(self):
        self.cursor.move_to(0, 0)
        self.timer.reset()
        self.target.setVisible(False)

    @transmitter()
    def finish(self):
        self.input_stream.finished.disconnect(self.stopped)
        self.input_stream.kill()
        self.input_stream.updated.disconnect(self.update)
        return

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()


if __name__ == '__main__':
    # from pytrigno import TrignoEMG
    # dev = TrignoEMG((0, 3), 200, host='192.168.1.114', units='normalized')
    from axopy.stream import EmulatedDaq
    dev = EmulatedDaq(rate=2000, num_channels=4, read_size=200)
    indev = InputStream(dev)

    b, a = butter(4, (10/2000./2., 450/2000./2.), 'bandpass')
    preproc_pipeline = copper.Pipeline([
        copper.Windower(400),
        copper.Centerer(),
        copper.Filter(b, a=a, overlap=200),
    ])
    main_pipeline = copper.Pipeline([
        preproc_pipeline,
        copper.CallablePipelineBlock(exg.mean_absolute_value),
        RLSMapping(4, 2, 0.99)
    ])

    Experiment(
        [
            SubjectSelection(extra_params=['hand']),
            Oscilloscope(preproc_pipeline),
            CursorFollowing(main_pipeline)
        ],
        device=indev
    ).run()
