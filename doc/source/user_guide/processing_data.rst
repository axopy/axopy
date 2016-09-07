.. _processing_data:

===============
Processing Data
===============

.. currentmodule:: axopy.pipeline

In axopy, data processing is implemented through a :class:`~.Pipeline`.
A pipeline is a series of processing routines for transforming raw input data
(e.g. electrophysiological data such as EMG) into useful output, such as the
velocity of a cursor on the screen. These routines can usually be broken down
into blocks which have common functionality.

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
actual processing involved in each can vary. axopy implements some of the
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

Windowing is handled by a :class:`~.Windower`.

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

Features in axopy are classes that take all of their parameters in ``__init__``
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

Connecting Blocks
-----------------

The :mod:`~.pipeline` module is a small infrastructure for processing data in
a pipeline style. You create or use the built-in :class:`~.PipelineBlock`
objects, then connect them up with an efficient (but still readable) syntax
with a :class:`~.Pipeline`.

The syntax for expressing pipeline structure is based on lists and tuples.
Lists hold elements that are connected in series::

    [a, b]:

        ─a─b─

The input is whatever ``a`` takes, and the output is whatever ``b`` outputs.
Tuples hold elements that are connected in parallel::

    (a, b):

         ┌─a─┐
        ─┤   ┝━
         └─b─┘

The input goes to *both* ``a`` and ``b``, and the output is whatever ``a`` and
``b`` output in a list. If we connect another element in series with a parallel
block, it must be a block that handles multiple inputs::

    [(a, b), c]:

         ┌─a─┐
        ─┤   ┝━c─
         └─b─┘

The bottom line is: pipeline blocks **accept** input types and they **specify**
the output types. You are responsible for ensuring that pipeline blocks can be
connected as specified.

Sometimes, you might want to pass the output of a block to some block structure
*and* somewhere downstream. To handle this case, there is
a :class:`~.PassthroughPipeline` that you can use as a block within another
pipeline::

    passthrough pipeline p ← (b, c):

         ┌─────┐
         ├─b─┐ │
        ─┤   ┝━┷━
         └─c─┘

    [a, p, d]:
                       ┌─────┐
                       ├─b─┐ │
        ─a─p━d─  →  ─a─┤   ┝━┷━d─
                       └─c─┘

The pass-through pipeline places its own output(s) after its input, so the
input is accesible on the other side. There are cases where this type of
structure is possible with a list/tuple expression, but sometimes the
pass-through pipeline as a block is needed. The above example is one of those
cases.


Implementing Pipeline Blocks
----------------------------

Pipeline blocks are simple to implement. It is only expected that you implement
a ``process()`` method which takes one argument (``data``) and returns
something. For multi-input blocks, you'll probably want to just expand the
inputs right off the bat (e.g. ``in_a, in_b = data``). Usually, the output is
some processed form of the input data::

    from axopy import pipeline

    class FooBlock(pipeline.PipelineBlock):
        def process(self, data):
            return data + 1

    class BarBlock(pipeline.PipelineBlock):
        def process(self, data):
            return 2 * data

With some blocks implemented, the list/tuple syntax described above is used for
specifying how they are connected::

    a = FooBlock()
    b = BarBlock()
    p = pipeline.Pipeline([a, b])

Now, you just give the pipeline input and get its output::

    input = 3
    result = p.process(input)

In this case, the result would be ``2 * (input + 1) == 8``.


Post-Process Hooks
------------------

Sometimes, it's useful to be able to hook into some block in the pipeline to
retrieve its data in the middle of a run through the pipeline. For instance,
let's say you have a simple pipeline::

    [a, b]:

        ─a─b─

You run some data through the pipeline to get the result from block ``b``, but
you also want to run some function with the output of ``a``. ``PipelineBlock``
takes a ``hooks`` keword argument which takes a list of functions to execute
after the block's ``process`` method finishes. To use hooks, make sure your
custom block calls the parent ``PipelineBlock`` ``__init__`` method. For
example::

    from axopy import pipeline

    class FooBlock(pipeline.PipelineBlock):
        def __init__(self, hooks=None):
            super(FooBlock, self).__init__(hooks=hooks)

        def process(self, data):
            return data + 1

    class BarBlock(pipeline.PipelineBlock):
        def process(self, data):
            return 2 * data

    def foo_hook(data):
        print("FooBlock output is %d".format(data))

    a = FooBlock(hooks=[foo_hook])
    b = BarBlock()

    p = pipeline.Pipeline([a, b])
    result = p.process(3)

Now, the call to ``process`` on the pipeline will input 3 to block ``a``, block
``a`` will add 1 then print ``FooBlock output is 4``, and then 4 will be passed
to block ``b``, which will return 8.
