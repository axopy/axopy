"""
The :mod:`axopy.features` module provides implementations of common
features in electrophysiological signal processing applications.
"""

from axopy.features.base import Feature
from axopy.features.time import MAV, WL, ZC, SSC, RMS

__all__ = ['Feature',
           'MAV',
           'WL',
           'ZC',
           'SSC',
           'RMS']
