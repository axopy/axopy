"""Some generic task implementations."""

from axopy.task import Task
from axopy import util
from axopy.messaging import transmitter
from axopy.gui.subject import ParticipantSelector
from axopy.gui.signals import SignalWidget


class Oscilloscope(Task):

    def __init__(self, pipeline=None):
        self.pipeline = pipeline

    def prepare_view(self, view):
        self.scope = SignalWidget()
        view.set_view(self.scope)

    def prepare_input_stream(self, input_stream):
        self.input_stream = input_stream
        self.input_stream.updated.connect(self.update)

    def run(self):
        self.input_stream.start()

    def update(self, data):
        if self.pipeline is not None:
            data = self.pipeline.process(data)
        self.scope.plot(data)

    def key_press(self, key):
        if key == util.key_return:
            self.finish()

    @transmitter()
    def finish(self):
        self.input_stream.kill()
        self.input_stream.updated.disconnect(self.update)
        return


class SubjectSelection(Task):

    def __init__(self, extra_params=None):
        self.extra_params = extra_params

    def prepare_view(self, view):
        self.ui = ParticipantSelector(extra_attrs=self.extra_params)
        self.ui.selected.connect(self._on_subject_selected)
        view.set_view(self.ui)

    def run(self):
        pass

    def _on_subject_selected(self, subject):
        self.select(subject)
        self.finish()

    @transmitter(('subject', dict))
    def select(self, subject):
        return subject
