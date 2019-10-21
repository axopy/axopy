"""Base task implementation and some generic tasks.

See the :ref:`user guide <task>` for information on implementing tasks.
"""

from axopy.task.base import Task
from axopy.task.common import Oscilloscope, BarPlotter, PolarPlotter

__all__ = ['Task', 'Oscilloscope', 'BarPlotter', 'PolarPlotter']
