.. image:: https://github.com/ucdrascal/axopy/raw/master/docs/_static/axopy.png
   :alt: AxoPy Logo

|

.. image:: https://travis-ci.org/ucdrascal/axopy.svg?branch=master
    :target: https://travis-ci.org/ucdrascal/axopy
    :alt: Travis CI Status

.. image:: https://readthedocs.org/projects/axopy/badge/?version=latest
   :target: http://axopy.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://codecov.io/gh/ucdrascal/axopy/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/ucdrascal/axopy
   :alt: Codecov test coverage

|

Axo-Pythonic synapses are those in which an axon synapses upon a Python
program. AxoPy aims to facilitate such connections between electrophysiolgical
signals and machines by making it easy for researchers to develop
human-computer interface experiments.

AxoPy consists of:

Graphical interface
    Central to AxoPy is the graphical user interface providing visual feedback
    to the subject and controlling the flow of the experiment. The GUI is
    backed by PyQt5, and you're free to implement customized graphical elements
    if those built in to AxoPy don't suit your needs.
Data acquisition
    AxoPy establishes a fairly simple API for communicating with input
    hardware, so all that's usually needed is a bit of middleware to get going.
    Check out pytrigno_ or pymcc_ to see what this is like. A couple input
    devices are built in (keyboard, noise generator), so examples run without
    needing special hardware.
Data storage
    Data is stored in a file structure with common file formats (CSV and HDF5)
    so you can a) start working with data as soon as an experiment session is
    over and b) you don't need anything but standard tools (pandas, h5py) to do
    so. A high-level interface to the storage structure is also provided to
    make traversing a dataset simple.
Pipeline processing
    Estimating intentions of the user from raw electrophysiological signals
    often involves a large number of processing operations. AxoPy facilitates
    flexible construction of pipelines that can be reused in different parts of
    an experiment and re-used for offline post-processing, etc.


Quickstart
==========

Installation
------------

pip
^^^

AxoPy is available on `PyPI`_, so the following should get it installed if
you're using a standard Python installation with ``pip``::

    $ pip install axopy

conda
^^^^^

AxoPy is not yet available on `conda-forge`, but it's not *too* bad to get it
installed at the moment.

Make sure you have a local copy of AxoPy. From the root directory of the
repository, you can create the conda environment with AxoPy's dependencies
installed::

    $ conda env create -f environment.yml

Now activate the environment:

- on Windows: run ``activate axopy`` in Anaconda Prompt
- on macOS or Linux: run ``source activate axopy`` in your terminal

Finally, with the environment activated, install AxoPy itself::

    (axopy) $ pip install .

See the `development documentation`_ for information on setting up
a development environment to work on AxoPy itself.

Hello, AxoPy
------------

Here's a minimal example to display some randomly generated signals in an
"oscilloscope":

.. code-block:: python

    from axopy.experiment import Experiment
    from axopy.task import Oscilloscope
    from axopy.stream import NoiseGenerator

    daq = NoiseGenerator(rate=1000, num_channels=4, read_size=100)
    Experiment(daq=daq).run(Oscilloscope())


Next Steps
----------

Check out the documentation_ for more information on creating experiments
(note: documentation is currently being reworked). Some `examples`_ are also
available.


Contributing
============

Please feel free to share any thoughts or opinions about the design and
implementation of this software by `opening an issue on GitHub
<https://github.com/ucdrascal/axopy/issues/new>`_. Constructive feedback is
welcomed and appreciated.

GitHub issues also serve as the support channel, at least for now. Questions
about how to do something are usually great opportunities to improve
documentation, so you may be asked about your thoughts on where the answers
should go.

If you want to contribute code, open a pull request. Bug fix pull requests are
always welcome. For feature additions, breaking changes, etc. check if there is
an open issue discussing the change and reference it in the pull request. If
there isn't one, it is recommended to open one with your rationale for the
change before spending significant time preparing the pull request.

Ideally, new/changed functionality should come with tests and documentation. If
you are new to contributing, it is perfectly fine to open a work-in-progress
pull request and have it iteratively reviewed. See the `development
documentation`_ for instructions on setting up a development environment,
running tests, and building the documentation.


.. _pytrigno: https://github.com/ucdrascal/pytrigno
.. _pymcc: https://github.com/ucdrascal/pymcc
.. _documentation: https://axopy.readthedocs.io
.. _examples: https://github.com/ucdrascal/axopy/tree/master/examples
.. _PyPI: https://pypi.org/
.. _conda-forge: https://conda-forge.org/
.. _conda: https://conda.io/docs/
.. _Riverbank: https://www.riverbankcomputing.com/software/pyqt/download5
.. _development documentation: http://axopy.readthedocs.io/en/latest/development.html
