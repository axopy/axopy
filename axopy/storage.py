"""Experiment data storage."""

# TODO implement trials.csv
# TODO come up with TaskStorage API
# TODO implement TaskStorage
# TODO write tests for TaskStorage
# TODO write tests for ArrayWriter
# TODO come up with ArrayReader API
# TODO implement ArrayReader
# TODO write tests for ArrayReader
# TODO come up with to_hdf5 functionality
# TODO implement to_hdf5
# TODO test to_hdf5
# TODO decide on supporting array attributes (e.g. channel names)

import os
import h5py
import numpy
import pandas
import zipfile
from axopy.util import makedirs


class Storage(object):
    """Top-level data storage maintainer.

    See the :ref:`user guide <storage>` for more information.

    Parameters
    ----------
    root : str, optional
        Path to the root of the data storage filestructure. By default, 'data'
        is used. If the directory doesn't exist, it is created.
    """

    def __init__(self, root='data'):
        self.root = root
        makedirs(root, exist_ok=True)
        self._subject_id = None

    @property
    def subject_ids(self):
        """Generate subject IDs found in storage sorted in alphabetical order.

        Returns
        -------
        subject_id : str
            ID of the subject found.
        """
        ls = os.listdir(self.root)
        for name in sorted(ls):
            path = os.path.join(self.root, name)
            if os.path.isdir(path):
                yield name

    @property
    def subject_id(self):
        """The current subject ID.

        When setting the subject ID for a new subject (i.e. one that doesn't
        exist already), storage for that subject is created.
        """
        return self._subject_id

    @subject_id.setter
    def subject_id(self, val):
        makedirs(os.path.join(self.root, val), exist_ok=True)
        self._subject_id = val

    @property
    def task_ids(self):
        """Generate names of tasks found for the current subject.

        Note that there may be no tasks found if the `subject_id` has not been
        set or if the subject hasn't started any tasks. In this case, nothing
        is yielded.
        """
        if self.subject_id is None:
            return

        subj_path = os.path.join(self.root, self.subject_id)
        ls = os.listdir(subj_path)
        for name in sorted(ls):
            path = os.path.join(subj_path, name)
            if os.path.isdir(path):
                yield name

    def create_task(self, task_id, column_names, array_names=None):
        """Creates a task for the current subject.

        Parameters
        ----------
        task_id : str
            The ID of the task to add. The name must not have been used for
            another task for the current subject.

        Returns
        -------
        writer : TaskWriter
            A new TaskWriter for storing task data.
        column_names : sequence
            A sequence of strings representing the columns of the trial data
            columns. Passed along to the TaskWriter.
        array_names : sequence, optional
            A sequence of strings representing the array types that will be
            stored. Passed along to TaskWriter. By default, no arrays are used.
        """
        path = self._task_path(task_id)

        try:
            makedirs(path)
        except FileExistsError:
            raise ValueError(
                "Subject {} has already started \"{}\". Only unique task "
                "names are allowed.".format(self.subject_id, task_id))

        return TaskWriter(path, task_id, column_names,
                          array_names=array_names)

    def require_task(self, task_id):
        """Retrieves a task for the current subject.

        Parameters
        ----------
        task_id :  str
            The ID of the task to look for. The task must have already been run
            with the current subject.

        Returns
        -------
        reader : TaskReader
            A new TaskReader for working with the existing task data.
        """
        if task_id not in self.task_ids:
            raise ValueError(
                "Subject {} has not started \"{}\" yet. Use `create_task` to "
                "create it first.".format(self.subject_id, task_id))

        path = self._task_path(task_id)
        return TaskReader(path, task_id)

    def to_zip(self, outfile):
        """Create a ZIP archive from a data storage hierarchy.

        For more information, see :func:`storage_to_zip`.
        """
        storage_to_zip(self.root, outfile)

    def to_hdf5(self, outfile):
        """Create a HDF5 file from the data storage hierarchy.

        Unlike :meth:`to_zip`, this method reorganizes the data to a more
        compact form.
        """
        pass

    def _task_path(self, task_id):
        return os.path.join(self.root, self.subject_id, task_id)


def read_hdf5(filepath, dataset='data'):
    """Read the contents of a dataset.

    This function assumes the dataset in the HDF5 file exists at the root of
    the file (i.e. at '/').

    Parameters
    ----------
    filepath : str
        Path to the file to read from.
    dataset : str, optional
        Name of the dataset to retrieve. By default, 'data' is used.

    Returns
    -------
    data : ndarray
        The data (read into memory) as a NumPy array. The dtype, shape, etc. is
        all determined by whatever is in the file.
    """
    with h5py.File(filepath, 'r') as f:
        return f.get('/{}'.format(dataset))[:]


def write_hdf5(filepath, data, dataset='data'):
    """Write data to an hdf5 file.

    The data is written to a new file with a single dataset called "data" in
    the root group.

    Parameters
    ----------
    filepath : str
        Path to the file to be written.
    data : ndarray
        NumPy array containing the data to write. The dtype, shape, etc. of the
        resulting dataset in storage is determined by this array directly.
    dataset : str, optional
        Name of the dataset to create. Default is 'data'.
    """
    with h5py.File(filepath, 'w') as f:
        f.create_dataset(dataset, data=data)


def read_csv(filepath):
    """Read the contents of a CSV data file into a pandas DataFrame.

    Parameters
    ----------
    filepath : str
        Path to the file to read from.

    Returns
    -------
    data : DataFrame
        A pandas DataFrame containing the trial data.
    """
    return pandas.read_csv(filepath)


class ArrayWriter(object):

    def __init__(self, filepath, orientation='horizontal'):
        self.filepath = filepath
        self.orientation = orientation
        self.data = None

    def stack(self, data):
        if self.data is None:
            self.data = data
        else:
            if self.orientation == 'vertical':
                self.data = numpy.vstack([self.data, data])
            else:
                self.data = numpy.hstack([self.data, data])

    def write(self, dataset):
        write_hdf5(self.filepath, self.data, dataset=dataset)
        self.clear()

    def clear(self):
        self.data = None


class TrialWriter(object):
    """Writes trial data to a CSV file line by line."""

    def __init__(self, path):
        self.path = path


class TaskWriter(object):
    """The main interface for creating a task dataset.

    Parameters
    ----------

    Attributes
    ----------
    array : dict
        Dictionary mapping names of arrays to the underlying ArrayWriter, which
        serves as a buffer to repeated stack data during a trial.
    """

    def __init__(self, root, task_id, column_names, array_names=None):
        self.task_id = task_id
        self.root = root
        self.column_names = column_names

        self._current_index = 0

        self.trial_writer = TrialWriter(os.path.join(root, 'trials.csv'))

        if array_names is None:
            array_names = []
        self.arrays = {n: ArrayWriter() for n in array_names}

    def finish_trial(self):
        self._current_index += 1

    def new_array(self, name, orientation='horizontal'):
        path = os.path.join(self.path, name)
        array = ArrayWriter(path, orientation=orientation)
        self.arrays[name] = array
        return array

    def write_trial(self, **data):
        for name, arr in self.arrays.items():
            arr.write(*self.counter.params)

        for col in self.columns:
            pass

        self.counter.next_trial()

    def next_block(self):
        self.counter.next_block()

    def finish(self):
        """Complete task data writing."""
        # TODO close the trials file
        pass


class TaskReader(object):

    def __init__(self, root, task_id):
        self.root = root
        self.task_id = task_id


def storage_to_zip(path, outfile=None):
    """Create a ZIP archive from a data storage hierarchy.

    The contents of the data storage hierarchy are all placed in the archive,
    with the top-level folder in the archive being the data storage root folder
    itself. That is, all paths within the ZIP file are relative to the dataset
    root folder.

    Parameters
    ----------
    path : str
        Path to the root of the dataset.
    outfile : str, optional
        Name of the ZIP file to create. If not specified, the file is created
        in the same directory as the data root with the same name as the
        dataset root directory (with ".zip" added).

    Returns
    -------
    outfile : str
        The name of the ZIP file created.
    """
    datapath, datadir = os.path.split(path)
    if outfile is None:
        # absolute path to parent of data root + dataset name + .zip
        outfile = os.path.join(datapath, datadir + '.zip')

    with zipfile.ZipFile(outfile, 'w') as zipf:
        for root, dirs, files in os.walk(path):
            for f in files:
                # write as *relative* path from data root
                zipf.write(os.path.join(root, f),
                           arcname=os.path.join(datadir, f))
    return outfile
