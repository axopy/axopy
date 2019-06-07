from axopy.features import waveform_length, logvar


class WaveformLength(object):
    def __init__(self):
        pass

    def compute(self, x):
        return waveform_length(x)


class LogVar(object):
    def __init__(self):
        pass

    def compute(self, x):
        return logvar(x)
