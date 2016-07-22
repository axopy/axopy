from hcibench.base import TaskUI
from hcibench.widgets import OscilloscopeWidget


class Oscilloscope(TaskUI):
    """
    Simple oscilloscope-like plugin for viewing signals in real-time.

    Parameters
    ----------
    pipeline : Pipeline, optional
        Processing pipeline to use before displaying data from the data
        acquisition device. If None, the raw data is not processed and is
        displayed as-is.
    name : str, optional
        Name of the plugin. If None, uses the class name.
    """

    def __init__(self, pipeline=None):
        super(Oscilloscope, self).__init__()

        self.pipeline = pipeline

        self.oscope_widget = OscilloscopeWidget()
        self.set_central_widget(self.oscope_widget)

    def setup_recorder(self):
        if self.pipeline is None:
            self.recorder.remove_pipeline()
        else:
            self.recorder.pipeline = self.pipeline
        self.recorder.updated.connect(self.on_recorder_update)

    def dispose_recorder(self):
        self.recorder.updated.disconnect(self.on_recorder_update)

    def on_recorder_update(self, data):
        self.oscope_widget.add_window(data)
