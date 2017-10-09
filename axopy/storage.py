import os
import h5py
import numpy
import pandas
import zipfile


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
        ensure_dir(self.path)

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
        ensure_dir(self.path)

        self.trials_path = os.path.join(self.path, 'trials')
        ensure_dir(self.trials_path)

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


class Storage(object):
    """Top-level storage object."""

    # TODO handle subject, session, etc.

    def __init__(self, root='.'):
        self.root = root

    def create_task(self, name, columns=None):
        task = TaskWriter(name)
        return task


class TaskWriter(object):

    def __init__(self, name, columns=None):
        self.trial_data = TrialWriter()
        self.arrays = {}

    def create_array(self, name):
        self.arrays[name] = ArrayWriter()


class Storage(object):

    def __init__(self, root='data', mode='a'):
        pass


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
