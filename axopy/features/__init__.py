from axopy.features.time import (mean_absolute_value, mean_value,
                                 waveform_length, wilson_amplitude,
                                 zero_crossings, slope_sign_changes,
                                 root_mean_square, integrated_emg, var, logvar,
                                 skewness, kurtosis, ar, sample_entropy,
                                 hjorth, histogram)

__all__ = ['mean_absolute_value',
           'mean_value',
           'waveform_length',
           'wilson_amplitude',
           'zero_crossings',
           'slope_sign_changes',
           'root_mean_square',
           'integrated_emg',
           'var',
           'logvar',
           'skewness',
           'kurtosis',
           'ar',
           'sample_entropy',
           'hjorth',
           'histogram']

# FIXME: fix string formatting in docstrings
import numpy
try:
    numpy.set_printoptions(legacy='1.13')
except TypeError:
    pass
