"""Experiment data storage."""

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
    def task_names(self):
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

    def create_task(self, name):
        """Creates a task for the current subject."""
        path = os.path.join(self.root, self.subject_id, name)
        try:
            makedirs(path)
        except FileExistsError:
            raise ValueError(
                "Subject {} has already started \"{}\". Only unique task "
                "names are allowed.".format(self.subject_id, name))
        # TODO create and return TaskWriter

    def require_task(self, name):
        if name not in self.task_names:
            raise ValueError(
                "Subject {} has not started \"{}\" yet. Use `create_task` to "
                "create it first.".format(self.subject_id, name))

        path = os.path.join(self.root, self.subject_id, name)
        # TODO create and return TaskReader

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


def read_hdf5(filepath):
    """Read the contents of the 'data' dataset into memory and return it.

    Parameters
    ----------
    filepath : str
        Path to the file to read from.

    Returns
    -------
    data : ndarray
        The data (read into memory) as a NumPy array. The dtype, shape, etc. is
        all determined by whatever is in the file.
    """
    with h5py.File(filepath, 'r') as f:
        return f.get('/data')[:]


def write_hdf5(filepath, data):
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
    """
    with h5py.File(filepath, 'w') as f:
        f.create_dataset('data', data=data)


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


class ArrayBuffer(object):

    def __init__(self, orientation='vertical'):
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

    def clear(self):
        self.data = None


class ArrayWriter(object):

    def __init__(self, path, orientation='horizontal'):
        self.path = path
        makedirs(self.path, exist_ok=True)

        self.buffer = ArrayBuffer(orientation=orientation)

    def stack(self, data):
        self.buffer.stack(data)

    def write(self, subject, block, trial):
        filename = self._gen_filename(subject, block, trial)
        filepath = os.path.join(self.path, filename)
        write_hdf5(filepath, self.buffer.data)
        self.clear()
        return filepath

    @property
    def data(self):
        return self.buffer.data

    def clear(self):
        self.buffer.clear()

    def _gen_filename(self, subject, block, trial):
        return 's{}_b{}_t{}.hdf5'.format(subject, block, trial)


class TaskCounter(object):

    def __init__(self, subj):
        self.subj = subj
        self.trial = 1
        self.block = 1

    def next_trial(self):
        self.trial += 1

    def next_block(self):
        self.block += 1
        self.trial = 1

    @property
    def params(self):
        return self.subj, self.block, self.trial


class TaskStorage(object):

    def __init__(self, task_name, subject, root='.', columns=None):
        self.task_name = task_name
        self.subject = subject
        self.root = root
        if columns is None:
            columns = []
        self.columns = columns
        self._init_dirs()
        self.counter = TaskCounter(subject)
        self.arrays = {}

    def _init_dirs(self):
        """Set up the global data paths for a task.

        This ensures that each experiment in the session gets its own
        subdirectory in data storage. Call just before running an experiment.
        """
        self.path = os.path.join(self.root, self.task_name)
        makedirs(self.path, exist_ok=True)

        self.trials_path = os.path.join(self.path, 'trials')
        makedirs(self.trials_path, exist_ok=True)

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


class TaskWriter(object):

    def __init__(self, name, columns=None):
        self.trial_data = TrialWriter()
        self.arrays = {}

    def create_array(self, name):
        self.arrays[name] = ArrayWriter()


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
