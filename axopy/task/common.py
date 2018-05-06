"""Some generic task implementations."""

from axopy.task import Task
from axopy import util
from axopy.messaging import transmitter
from axopy.gui.graph import SignalWidget


class Oscilloscope(Task):

    def __init__(self, pipeline=None):
        super(Oscilloscope, self).__init__()
        self.pipeline = pipeline

    def prepare_graphics(self, container):
        self.scope = SignalWidget()
        container.set_widget(self.scope)

    def prepare_input_stream(self, input_stream):
        self.input_stream = input_stream
        self.connect(self.input_stream.updated, self.update)

    def run(self):
        self.input_stream.start()

    def update(self, data):
        if self.pipeline is not None:
            data = self.pipeline.process(data)
        self.scope.plot(data)

    def key_press(self, key):
        if key == util.key_return:
            self.finished()

    def finish(self):
        self.input_stream.kill()
