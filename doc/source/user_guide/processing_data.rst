.. _processing_data:

===============
Processing Data
===============

In AxoPy, data processing is implemented using copper_. A pipeline is a series
of processing routines for transforming raw input data (e.g.
electrophysiological data such as EMG) into useful output, such as the velocity
of a cursor on the screen. These routines can usually be broken down into
blocks which have common functionality.

Common Blocks
-------------

The typical picture for an electrophysiological signal processing pipeline
looks something like::

             Input
               ↓
    ┌──────────────────────┐
    │       Windowing      │
    └──────────────────────┘
               ↓
    ┌──────────────────────┐
    │     Conditioning     │
    └──────────────────────┘
               ↓
    ┌──────────────────────┐
    │  Feature Extraction  │
    └──────────────────────┘
               ↓
    ┌──────────────────────┐
    │  Intent Recognition  │
    └──────────────────────┘
               ↓
    ┌──────────────────────┐
    │    Output Mapping    │
    └──────────────────────┘
               ↓
             Output

Each block in this example is really a *type* of processing block, and the
actual processing involved in each can vary. AxoPy implements some of the
common cases, but creating custom blocks and connecting them together in
a pipeline structure is simple. Also, the picture above shows a simple series
structure, where each block takes input only from the block before it. More
complex structures are sometimes convenient or necessary, and some complexity
is supported.

Windowing
^^^^^^^^^

Windowing involves specifying a time window over which the rest of the pipeline
will operate. That is, a windower keeps track of the current input data and
optionally some data from the past, concatentating the two and passing it
along. This is useful for calculating statistics over a sufficient sample size
while updating the pipeline output at a rapid rate, achieved by overlapping
windows. In an offline processing context (i.e. processing static recordings),
windowing also specifies how much data to read in on each iteration through the
recording.

Conditioning
^^^^^^^^^^^^

Raw data conditioning (or pre-processing) usually involves things like
filtering and normalization. Usually the output of a conditioning block does
not fundamentally change the representation of the input.

Feature Extraction
^^^^^^^^^^^^^^^^^^

Features are statistics computed on a window of input data. Generally, they
should represent the information contained in the raw input in a compact way.
For example, you might take 100 samples of data from six channels of EMG and
calculate the root-mean-square value of each channel during that 100-sample
window of time. This results in an array of length 6 which represents the
amplitude of each channel in the high-dimensional raw data. A feature extractor
is just a collection of features to compute from the input.

Features in AxoPy are classes that take all of their parameters in ``__init__``
and perform their operation on the input in a ``compute`` method.

Features are typically used by adding a handful of them to
a :class:`~.FeatureExtractor` and putting that extractor in
a :class:`~.Pipeline`.

Intent Recognition
^^^^^^^^^^^^^^^^^^

Intent recognition is the prediction or estimation of what the user intends to
do based on the signals generated. An example would be a large signal sensed at
the group of extensor muscles in the forearm for communicating "wrist
extension." Sometimes this mapping can be specified a priori, but most of the
time we rely on machine learning techniques to infer this mapping from training
data.


.. _copper: https://github.com/ucdrascal/copper
