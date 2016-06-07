from hcibench.base import Plugin

from hcibench.templates.oscilloscope import Ui_Oscilloscope


class Oscilloscope(Plugin):
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

    def __init__(self, pipeline=None, name=None):
        super(Oscilloscope, self).__init__(name=name)

        self.ui = Ui_Oscilloscope()
        self.ui.setupUi(self)

        self.pipeline = pipeline

    def setup_recorder(self):
        if self.pipeline is None:
            self.recorder.remove_pipeline()
        else:
            self.recorder.pipeline = self.pipeline
        self.recorder.updated.connect(self.on_recorder_update)

    def dispose_recorder(self):
        self.recorder.updated.disconnect(self.on_recorder_update)

    def on_recorder_update(self, data):
        self.ui.graphicsLayout.add_window(data)
