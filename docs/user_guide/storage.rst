.. _storage:

============
Data Storage
============

.. currentmodule:: axopy.storage

Data is stored in a hierarchical fashion using a specific file structure and
common file types. There are two types of files: comma separated value (CSV)
files for *trial data* (one row per trial) and HDF5 files for *array data* (one
file per trial). Here's the file structure in abstract terms::

    data_root/
        subject_id/
            task_id/
                file: trials.csv
                array_type/
                    file: 1.hdf5
                    file: 2.hdf5
                    ...

You have the root of the entire dataset, containing a subfolder for each
subject. Each subject folder contains a set of subfolders, one per task. The
task subfolders contain a single CSV file which contains all of the
*attributes* (scalars) for each trial, and it contains subfolders for each type
of array data. These array data subfolders contain an HDF5 file per trial.

As an concrete example, suppose you are running an experiment where subjects
are tasked with contracting a muscle to a specified level, determined using
electromyography (EMG). For each trial, you want to store the following:

- the time it took for the subject to reach the desired contraction level for
  each trial
- the number of times the contraction level went past the desired level
  (overshoots)
- the raw EMG signals, which are recorded at 2 kHz
- the current "level of contraction," which is computed by processing the EMG
  signals through some processing pipeline you have set up at 10 Hz

The trial data variables here are time to target and overshoots, so these are
placed in a CSV file with one row per trial:

===== ============== ==========
index time_to_target overshoots
===== ============== ==========
0     3.271942       1
1     2.159271       0
2     3.212450       2
===== ============== ==========

Since you have two different array-like entities to store (raw EMG data at
2 kHz and processed position at 10 Hz), you create two different array types:
``emg`` and ``level``. They are placed in separate subfolders of the task and
each one is stored as an array in a HDF5 file, one file per trial. The result
of all of this is a structure that looks like::

    data_root/
        subject_id/
            contraction_level_task/
                file: trials.csv
                emg/
                    file: 1.hdf5
                    file: 2.hdf5
                    ...
                level/
                    file: 1.hdf5
                    file: 2.hdf5
                    ...

The HDF5 format was chosen for all array data because it naturally works with
NumPy arrays, which are the assumed container for data as it goes from
a hardware device through processing code to computer interaction. It also
saves the arrays in a binary format instaed of converting to strings as
something like ``numpy.savetxt`` would do, potentially reducing the size of
a whole experiment's dataset significantly if you store many arrays
representing high-frequency electrophysiological recordings.

The goals of this storage layout are to be simple to implement and reason
about, to allow for manual browsing of the dataset, and to enable simultaneous
sessions (i.e. multiple researchers running the experiment with different
subjects) with a very simple and intuitive data merging procedure (i.e. just
designate a single root folder and move all subject data there). The layout is
*not* optimized for processing and analyzing data once an experiment is
complete, however. For that, see :ref:`data-consolidation`.


.. _experiment-storage:

Experiment-Level Storage
========================

The top-level :class:`Storage` class handles the first two layers of the
storage hierarchy: subjects and tasks. It is initialized at the beginning of
each session and (e.g. once per subject for a single-session experiment) and
the data storage hierarchy is built for each subject. Initializing and adding
subjects is typically handled for you by :class:`axopy.experiment.Experiment`
in the context of running an experiment. Once a task is given access to the
:class:`Storage` object, however, it is up to the task implementation to set up
:class:`TaskReader` objects for reading data from other tasks and
:class:`TaskWriter` objects for storing its own data. This is done by calling
:meth:`Storage.require_task` and :meth:`Storage.create_task`, respectively.


.. _task-storage:

Task Storage
============

Task storage is designed to make implementing a task's data reading and writing
as simple as possible, while being flexible enough to accommodate different
kinds of experimental design. If you are interested in processing data after an
experiment has been run, see the :ref:`data-consolidation` documentation.


.. _data-consolidation:

Data Consolidation
==================

Most of the data reading and writing functionality implemented in AxoPy is
designed to make implementing an experiment as easy as possible, but there are
some convenience functions for compiling an experiment's dataset into something
more amenable to post-processing and analysis.

Archiving Raw Data
------------------

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
---------------

In addition to archiving raw data, you'll probably want what I'll call
a "working dataset," one in which you can read from, do some processing, write
back to, etc. The main purpose here is to compactly and neatly store an entire
dataset while allowing for more saved analysis to be done once the experiment
is complete. The primary routine is :func:`storage_to_hdf5`, which traverses
the data contained in the root storage directory and consolidates everything
into a single HDF5 file.
