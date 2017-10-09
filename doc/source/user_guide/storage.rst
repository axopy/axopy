.. _storage:

============
Data Storage
============

.. _currentmodule:: axopy.storage

The top-level :class:`StorageWriter` is intended for use when running an
experiment. It is designed to be initialized multiple times (essentially once
per subject) and the data storage hierarchy is built for each subject. 


.. _task-storage

Task Storage
------------

Task storage is designed to make implementing a task's data reading and writing
as simple as possible, while being flexible enough to accommodate different
kinds of experimental design. If you are interested in processing data after an
experiment has been run, see the :ref:`data-consolidation` documentation.


.. _data-consolidation

Data Consolidation
------------------

Most of the data reading and writing functionality implemented in AxoPy is
designed to make implementing an experiment as easy as possible, but there are
some convenience functions for compiling an experiment's dataset into something
more amenable to post-processing and analysis.

Archiving Raw Data
^^^^^^^^^^^^^^^^^^

In most cases, you'll want to archive your entire untouched dataset once an
experiment is complete, or maybe even periodically as an experiment is
performed. For this purpose, there is  the :func:`storage_to_zip` function,
which creates a ZIP archive of the data contained in the root storage
directory. It's usage is fairly simple, since it does a simple task. You pass
it the path to your data storage root directory, which can be relative to the
directory you run the function from. Let's say you have some data in a folder
called ``experiment01_data``::

    >>> from axopy.storage import storage_to_zip
    >>> storage_to_zip('experiment01_data')

There should now be a file called ``experiment01_data.zip`` in the current
directory, containing a copy of the whole dataset hierarchy. You can also
specify an output file if you don't like the default::

    >>> from axopy.storage import storage_to_zip
    >>> storage_to_zip('experiment01_data', outfile='dataset.zip')

Working Dataset
^^^^^^^^^^^^^^^

In addition to archiving raw data, you'll probably want what I'll call
a "working dataset," one in which you can read from, do some processing, write
back to, etc. The main purpose here is to compactly and neatly store an entire
dataset while allowing for more saved analysis to be done once the experiment
is complete. The primary routine is :func:`storage_to_hdf5`, which traverses
the data contained in the root storage directory and consolidates everything
into a single HDF5 file.
