Data Storage
============

Experiment data is stored in HDF5_ files using h5py_. HDF5 is a relatively
simple storage format to understand, and it can mostly be thought of as
identical to a file system. There are groups (analogous to folders) and
datasets (analogous to files). So, groups contain other groups and datasets,
and datasets contain data. In axopy, a basic structure is imposed to make the
library capable of inspecting and visualizing experiment files.

::

    /participants/
        <particpiant_id>/
            <task_name>/
                <run_name>/
                    dataset(s) specified by the task implementation
                <run_name>/
                    dataset(s) specified by the task implementation
            <task_name>/
                <run_name>/
                    dataset(s) specified by the task implementation
                <run_name>/
                    dataset(s) specified by the task implementation





.. _hdf5: https://www.hdfgroup.org/
.. _h5py: http://www.h5py.org/
