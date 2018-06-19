.. _installation:

============
Installation
============

There are two major options for installing AxoPy: pip and (Ana)conda.

.. seealso:: If you're interested in developing AxoPy itself, see the
   :ref:`development` documentation.


pip
===

If you like to use a systemwide Python installation (such as the Python
provided by your package manager on Linux or the official installer for
Windows), you can use pip to install AxoPy from PyPI_::

    $ pip install axopy

You may also want to make use of venv_ to create a virtual environment first.
This would allow you to install several different versions of AxoPy for
different projects, for example::

    $ python -m venv .venv
    $ source .venv/bin/activate
    (.venv) $ pip install axopy

Note that the second command above depends on your platform. See the venv_
documentation for more information.

.. _PyPI: https://pypi.org/
.. _venv: https://docs.python.org/3/tutorial/venv.html


conda
=====

AxoPy can also be installed with miniconda_ or Anaconda_ via the conda-forge_
channel::

    $ conda install -c conda-forge axopy

Similarly to the instructions above for pip installation, you may want to
create a separate conda environment before installing::

    $ conda create -c conda-forge -n axopy axopy

.. _miniconda: http://conda.pydata.org/miniconda.html
.. _Anaconda: https://anaconda.org/
.. _conda-forge: https://conda-forge.org/
