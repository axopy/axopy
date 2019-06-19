from axopy.features import (waveform_length, logvar, ar, wilson_amplitude,
                            slope_sign_changes)


class WaveformLength(object):
    def __init__(self):
        pass

    def compute(self, x):
        return waveform_length(x, axis=1, keepdims=False)


class LogVar(object):
    def __init__(self):
        pass

    def compute(self, x):
        return logvar(x, axis=1, keepdims=False)


class AR(object):
    def __init__(self, order):
        self.order = order

    def compute(self, x):
        return ar(x, order=self.order, axis=1, keepdims=False)


class WilsonAmplitude(object):
    def __init__(self, threshold):
        self.threshold = threshold

    def compute(self, x):
        return wilson_amplitude(x, threshold=self.threshold, axis=1,
                                keepdims=False)


class SlopeSignChanges(object):
    def __init__(self, threshold):
        self.threshold = threshold

    def compute(self, x):
        return slope_sign_changes(x, threshold=self.threshold, axis=1,
                                  keepdims=False)
