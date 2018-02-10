"""Data streams for processing with a pipeline."""

import warnings
import numpy as np


def segment(data, length, overlap=0):
    """Generate segments of an array.

    Each segment is of a specified length and optional overlap with the
    previous segment. Only segments of the specified length are retrieved (if
    segments don't fit evenly into the data).

    Parameters
    ----------
    data : array, shape (n_channels, n_samples)
        Data to segment.
    length : int
        Number of samples to retrieve in each chunk.
    overlap : int, optional
        Number of overlapping samples in consecutive chunks.

    Yields
    ------
    segment : array (n_channels, length)
        Segment of the input array.

    Examples
    --------
    Segment a 2-channel recording:

    >>> import numpy as np
    >>> from axopy.pipeline import segment
    >>> x = np.arange(8).reshape(2, 4)
    >>> x
    array([[0, 1, 2, 3],
           [4, 5, 6, 7]])
    >>> seg = segment(x, 2)
    >>> next(seg)
    array([[0, 1],
           [4, 5]])
    >>> next(seg)
    array([[2, 3],
           [6, 7]])

    Consecutive segments with overlapping samples agree:

    >>> seg = segment(x, 3, overlap=2)
    >>> next(seg)
    array([[0, 1, 2],
           [4, 5, 6]])
    >>> next(seg)
    array([[1, 2, 3],
           [5, 6, 7]])
    """
    data = np.atleast_2d(data)
    n = data.shape[1]
    for f, t in segment_indices(n, length, overlap=overlap):
        yield data[:, f:t]


def segment_indices(n, length, overlap=0):
    """Generate indices to segment an array.

    Each segment is of a specified length with optional overlap with the
    previous segment. Only segments of the specified length are retrieved if
    they don't fit evenly into the the total length. The indices returned are
    meant to be used for slicing, e.g. ``data[:, from:to]``.

    Parameters
    ----------
    n : int
        Number of samples to segment up.
    length : int
        Length of each segment.
    overlap : int, optional
        Number of overlapping samples in consecutive segments.

    Yields
    ------
    from : int
        Index of the beginning of the segment with respect to the input array.
    to : int
        Index of the end of the segement with respect to the input array.

    Examples
    --------
    Basic usage -- segment a 6-sample recording into segments of length 2:

    >>> import numpy as np
    >>> from axopy.pipeline import segment_indices
    >>> list(segment_indices(6, 2))
    [(0, 2), (2, 4), (4, 6)]

    Overlapping segments:

    >>> list(segment_indices(11, 5, overlap=2))
    [(0, 5), (3, 8), (6, 11)]
    """
    skip = length - overlap

    if (n - length) % skip != 0:
        warnings.warn("Data (length {}) cannot be chunked evenly into "
                      "segments of length {} with overlap {}".format(
                          n, length, overlap),
                      UserWarning)

    for i in range(0, n, skip):
        if i + length <= n:
            yield i, i + length
