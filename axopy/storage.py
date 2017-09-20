import os
import h5py
import numpy
import pandas


data_root = 'data'


def ensure_dir(path):
    """Ensure a directory exists. If it doesn't, create it.

    Also creates all intermediate directories if necessary.

    Parameters
    ----------
    path : str
        Path to directory to create.
    """
    try:
        os.makedirs(path)
    except OSError:
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

    def add(self, data):
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
        ensure_dir(self.path)

        self.buffer = ArrayBuffer(orientation=orientation)

    def add(self, data):
        self.buffer.add(data)

    def write(self, subject, block, trial):
        filename = self._gen_filename(subject, block, trial)
        filepath = os.path.join(self.path, filename)
        write_hdf5(filepath, self.buffer.data)
        self.clear()
        return filepath

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
        self._init_dirs()
        self.counter = TaskCounter(subject)
        self.arrays = {}

    def _init_dirs(self):
        """Set up the global data paths for a task.

        This ensures that each experiment in the session gets its own
        subdirectory in data storage. Call just before running an experiment.
        """
        self.path = os.path.join(self.root, self.task_name)
        ensure_dir(self.path)

        self.trials_path = os.path.join(self.path, 'trials')
        ensure_dir(self.trials_path)

    def new_array(self, name, orientation='horizontal'):
        path = os.path.join(self.path, name)
        array = ArrayWriter(path, orientation=orientation)
        self.arrays[name] = array
        return array

    def write_trial(self, data):
        for name, arr in self.arrays.items():
            arr.write(*self.counter.params)
        self.counter.next_trial()

    def next_block(self):
        self.counter.next_block()
