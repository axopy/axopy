from axopy.features.time import (mean_absolute_value, waveform_length,
                                 zero_crossings, slope_sign_changes,
                                 root_mean_square, integrated_emg, logvar)

__all__ = ['mean_absolute_value',
           'waveform_length',
           'zero_crossings',
           'slope_sign_changes',
           'root_mean_square',
           'integrated_emg',
           'logvar']

# FIXME: fix string formatting in docstrings
import numpy
try:
    numpy.set_printoptions(legacy='1.13')
except TypeError:
    pass
