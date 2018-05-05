"""Experiment data storage."""

import os
import h5py
import numpy
import pandas
import zipfile
import shutil
import pickle
import logging


#
# Highest layer. Used by tasks to obtain task readers/writers
#

class Storage(object):
    """Top-level data storage maintainer.

    See the :ref:`user guide <storage>` for more information.

    Parameters
    ----------
    root : str, optional
        Path to the root of the data storage filestructure. By default, 'data'
        is used. If the directory doesn't exist, it is created.
    allow_overwrite : bool, optional
        Specified whether or not the storage interface allows you to overwrite
        a task's data for a subject if it already exists.
    """

    def __init__(self, root='data', allow_overwrite=False):
        self.root = root
        self.allow_overwrite = allow_overwrite
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

    def create_task(self, task_id):
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
        """
        path = self._task_path(task_id)

        try:
            makedirs(path)
        except OSError:
            if self.allow_overwrite:
                shutil.rmtree(path)
                makedirs(path)
            else:
                raise ValueError(
                    "Subject {} has already started \"{}\". Only unique task "
                    "names are allowed.".format(self.subject_id, task_id))

        return TaskWriter(path)

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

    def _task_path(self, task_id):
        return os.path.join(self.root, self.subject_id, task_id)


#
# Middle layer. Used by tasks to read/write data.
#

class TaskWriter(object):
    """The main interface for storing data from a task.

    Parameters
    ----------
    root : str
        Path to the task root (e.g. 'data/subject_1/taskname').

    Attributes
    ----------
    trials : TrialWriter
        :class:`TrialWriter` for storing trial data.
    """

    def __init__(self, root):
        self.root = root
        self.trials = TrialWriter(_trials_path(self.root))

    def write(self, trial):
        """Write trial data.

        This must be the last thing done for the current trial. That is, make
        sure all arrays have accumulated all data required. This method flushes
        trial and array data to files for you.

        **Important note**: The trial's arrays are cleared after writing.

        Parameters
        ----------
        trial : Trial
            Tral data. See :meth:`TrialWriter.write` and :class:`Trial` for
            details.
        """
        self.trials.write(trial.attrs)

        ind = self.trials.df.index[-1]
        for name, array in trial.arrays.items():
            path = _array_path(self.root, name)
            write_hdf5(path, array.data, dataset=str(ind))
            array.clear()

        logging.info('saving trial {}:{}\n{}'.format(
            trial.attrs['block'], trial.attrs['trial'], str(trial)))

    def pickle(self, obj, name):
        """Write a generic object to storage.

        This can be useful to persist an object from one task to another, or to
        store something that doesn't easily fit into the AxoPy storage model
        (trial attributes and arrays). Be cautious, however, as pickles are not
        the best way to store things long-term nor securely. See the advice
        given here, for example:
        http://scikit-learn.org/stable/modules/model_persistence.html

        Parameters
        ----------
        obj : object
        return obj
            The object to pickle.
        name : str
            Name of the pickle to save (no extension).
        """
        with open(_pickle_path(self.root, name), 'wb') as f:
            pickle.dump(obj, f)


class TaskReader(object):
    """High-level interface to task storage.

    Parameters
    ----------
    root : str
        Path to task's root directory. This is the directory specific to a task
        which contains a ``trials.csv`` file and HDF5 array files.

    Attributes
    ----------
    trials : DataFrame
        A Pandas DataFrame representing the trial data.
    """

    def __init__(self, root):
        self.root = root
        self._trials = None

    @property
    def trials(self):
        if self._trials is None:
            self._trials = pandas.read_csv(_trials_path(self.root))
        return self._trials

    def iterarray(self, name):
        """Iteratively retrieve an array for each trial.

        Parameters
        ----------
        name : str
            Name of the array type.
        """
        for ind in self.trials.index:
            dset = str(ind)
            yield read_hdf5(_array_path(self.root, name), dataset=dset)

    def array(self, name):
        """Retrieve an array type's data for all trials."""
        return numpy.vstack(self.iterarray(name))

    def pickle(self, name):
        """Load a pickled object from storage.

        Parameters
        ----------
        name : str
            Name of the pickled object (no extension).
        """
        with open(_pickle_path(self.root, name), 'rb') as f:
            obj = pickle.load(f)
            return obj


#
# Lowest layer. Used by TaskReader/TaskWriter.
#

class TrialWriter(object):
    """Writes trial data to a CSV file line by line.

    Parameters
    ----------
    filepath : str
        Path to the file to create.

    Attributes
    ----------
    data : dict
        Dictionary containing all trial data written so far.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.data = {}

    def write(self, data):
        """Add a single row to the trials dataset.

        Data is immediately added to the file on disk.

        Parameters
        ----------
        data : dict
            Data values to add.
        """
        for col, val in data.items():
            if col not in self.data:
                self.data[col] = []
            self.data[col].append(val)

        self.df = pandas.DataFrame(self.data)
        self.df.to_csv(self.filepath, index=False)


#
# Utilities
#

def _trials_path(taskroot):
    return os.path.join(taskroot, 'trials.csv')


def _array_path(taskroot, arrayname):
    return os.path.join(taskroot, '{}.hdf5'.format(arrayname))


def _pickle_path(taskroot, picklename):
    return os.path.join(taskroot, '{}.pkl'.format(picklename))


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
    with h5py.File(filepath, 'a') as f:
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


def makedirs(path, exist_ok=False):
    """Recursively create directories.

    This is needed for Python versions earlier than 3.2, otherwise
    ``os.makedirs(path, exist_ok=True)`` would suffice.

    Parameters
    ----------
    path : str
        Path to directory to create.
    exist_ok : bool, optional
        If `exist_ok` is False (default), an exception is raised. Set to True
        if it is acceptable that the directory already exists.
    """
    try:
        os.makedirs(path)
    except OSError:
        if not exist_ok:
            raise
