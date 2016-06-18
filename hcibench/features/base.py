"""
Base classes for all features.

Subclasses of Feature should implement a ``compute`` method, which assumes the
input is an array of shape (n_channels, n_samples).
"""


class Feature(object):
    pass
