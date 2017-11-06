"""Experiment data storage."""

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

        return TaskWriter(path, column_names, array_names=array_names)

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
        return TaskReader(path)

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


class ArrayWriter(object):
    """Buffered array data backed by HDF5.

    The `ArrayWriter` is responsible for "stacking" data into an array and
    writing it to disk all at once. Once an array is written, the buffer is
    cleared and you can write another array. All arrays are written to a single
    HDF5 file with a given dataset name.

    Parameters
    ----------
    filepath : str
        Path to the HDF5 file that will store the arrays.
    orientation : str, optional
        Orientation of stacking. If 'vertical', data is stacked vertically
        (i.e. along axis 1), otherwise it is stacked horizontally.

    Attributes
    ----------
    data : ndarray
        Data that has been buffered so far. Can be set directly if you don't
        want to use the stacking mechanism to accumulate data.
    """

    def __init__(self, filepath, orientation='horizontal'):
        self.filepath = filepath
        self.orientation = orientation

        self.data = None

    def stack(self, data):
        """Stack new data onto the current buffer.

        Parameters
        ----------
        data : ndarray
            The data to stack. Must be of a compatible shape with the existing
            buffer. For example, if stacking horizontally, the number of rows
            must be consistent on each call to `stack`, but the number of
            columns doesn't matter.
        """
        if self.data is None:
            self.data = data
        else:
            if self.orientation == 'vertical':
                self.data = numpy.vstack([self.data, data])
            else:
                self.data = numpy.hstack([self.data, data])

    def write(self, dataset):
        """Write the contents of the buffer to a new dataset in the HDF5 file.

        The HDF5 dataset is created in the root group.

        Parameters
        ----------
        dataset : str
            Name of the dataset to create in the HDF5 flie.
        """
        write_hdf5(self.filepath, self.data, dataset=dataset)
        self.clear()

    def clear(self):
        """Clears the buffer.

        Anything that was in the buffer is not retrievable.
        """
        self.data = None


class TrialWriter(object):
    """Writes trial data to a CSV file line by line.

    Parameters
    ----------
    filepath : str
        Path to the file to create.
    columns : sequence
        Column names.
    """

    def __init__(self, filepath, columns):
        self.filepath = filepath
        self.columns = columns

        self._data = {col: [] for col in self.columns}

    @property
    def data(self):
        """A pandas DataFrame containing all of the data."""
        return pandas.DataFrame(self._data, columns=self.columns)

    def write(self, data):
        """Add a single row to the trials dataset.

        Data is immediately added to the file on disk.

        Parameters
        ----------
        data : sequence or dict
            Data values to add. If a sequence (e.g. list, tuple), it is assumed
            there are as many values as columns and the values are assumed to
            be in the same order as the columns. If a dictionary, it is assumed
            enough items are given.
        """
        if isinstance(data, dict):
            it = data.items()
        else:
            it = zip(self.columns, data)

        for col, val in it:
            self._data[col].append(val)

        self.data.to_csv(self.filepath, index=False)


class TaskWriter(object):
    """The main interface for creating a task dataset.

    Parameters
    ----------

    Attributes
    ----------
    trials : TrialWriter
        :class:`TrialWriter` for storing trial data.
    arrays : dict
        Dictionary mapping names of arrays to the underlying
        :class:`ArrayWriter`, which serves as a buffer to repeated stack data
        during a trial.
    """

    def __init__(self, root, column_names, array_names=None):
        self.root = root
        self.column_names = column_names

        if array_names is None:
            array_names = []
        self.array_names = array_names

        self.trials = TrialWriter(os.path.join(self.root, 'trials.csv'),
                                  self.column_names)

        self.arrays = {}
        for name in self.array_names:
            path = os.path.join(root, '{}.hdf5'.format(name))
            self.arrays[name] = ArrayWriter(path)

    def write(self, trial):
        """Write trial data.

        This must be the last thing done for the current trial. That is, make
        sure all arrays have accumulated all data required. This method flushes
        trial and array data to files for you.

        Parameters
        ----------
        trial : sequence or dict
            Tral data. See :meth:`TrialWriter.write` for details.
        """
        self.trials.write(trial)

        dset = str(self.trials.data.index[-1])
        for array_writer in self.arrays.values():
            array_writer.write(dset)


class TaskReader(object):

    def __init__(self, root):
        self.root = root


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
