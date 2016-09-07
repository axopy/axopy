"""
The :mod:`axopy.features` module provides implementations of common
features in electrophysiological signal processing applications.
"""

from .base import Feature
from .time import MAV, WL, ZC, SSC, RMS

__all__ = ['Feature',
           'MAV',
           'WL',
           'ZC',
           'SSC',
           'RMS']
