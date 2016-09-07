"""
The :mod:`axopy.pipeline` module provides a flexible infrastructure for
data processing and implements some common types of processing blocks.
"""

from .base import PipelineBlock, Pipeline, PassthroughPipeline
from .common import Windower, Filter, FeatureExtractor, Estimator, Transformer

__all__ = ['PipelineBlock',
           'Pipeline',
           'PassthroughPipeline',
           'Windower',
           'Filter',
           'FeatureExtractor',
           'Estimator',
           'Transformer']
