.. _installation:

============
Installation
============

Here are the main ways to get started with AxoPy. Once the project is more
mature, it should be much easier through installing directly with pip and/or
conda.


Miniconda
---------

Install miniconda_, create an environment with the dependencies, then install
AxoPy.

::

    $ conda create -n axopy numpy scipy scikit-learn h5py pyqt
    $ source activate axopy
    (axopy)$ pip install git+https://github.com/pyqtgraph/pyqtgraph.git
    (axopy)$ python setup.py install


venv
----

Here's how you can set up a virtual environment and install AxoPy using venv_.
This installation will allow you to use most of AxoPy's features. Exceptions
include interacting with some data acquisition devices (see the :ref:`User
Guide <daq>` for details).

::

   $ python -m venv .venv
   $ source .venv/bin/activate
   (.venv) $ pip install numpy scipy scikit-learn h5py pyqt5
   (.venv) $ pip intall git+https://github.com/pyqtgraph/pyqtgraph.git
   (.venv) $ python setup.py install


tox
---

Testing is done with tox_. There is also a tox directive for creating a
virtualenv that should have everything needed for developing and testing AxoPy.

::

   $ tox -e mkvenv
   $ source .venv/bin/activate


.. _miniconda: http://conda.pydata.org/miniconda.html
.. _venv: https://docs.python.org/3/library/venv.html
.. _tox: https://tox.readthedocs.io/en/latest/
