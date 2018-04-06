import pytest
import os
import numpy
import pandas
from axopy.storage import (Storage, TaskWriter, ArrayWriter, TrialWriter,
                           read_hdf5, write_hdf5, storage_to_zip)


@pytest.fixture(scope='function')
def tmpdirpath(tmpdir):
    """Convenience fixture to get the path to a temporary directory."""
    return str(tmpdir.dirpath())


def test_storage(tmpdirpath):
    """Integration test for regular storage usage."""
    # usually done by task manager
    storage = Storage(root=tmpdirpath)
    storage.subject_id = 'p0'

    # task 1 implementation
    writer = storage.create_task('task1', ['trial', 'label'],
                                 array_names=['data'])
    writer.arrays['data'].stack(numpy.array([0, 1, 2]))
    writer.arrays['data'].stack(numpy.array([3, 4, 5]))
    writer.write([0, 'label1'])

    # task 2 implementation
    storage.require_task('task1')
    writer = storage.create_task('task2', ['trial', 'success'])
    # TODO do something with the reader
    writer.write([0, True])
    writer.write([1, False])


def test_storage_directories(tmpdir_factory):
    """Test that Storage can find and create the right directories."""
    # create a file structure:
    #    data/
    #        p0/
    #            task1/
    #            task2/
    #        p1/
    #            task1/
    #        p2/
    root = str(tmpdir_factory.mktemp('data'))

    folders = {'p0': ['task1', 'task2'], 'p1': ['task1'], 'p2': []}

    for subj_id, tasknames in folders.items():
        os.makedirs(os.path.join(root, subj_id))
        for name in tasknames:
            os.makedirs(os.path.join(root, subj_id, name))

    storage = Storage(root)

    assert list(storage.subject_ids) == sorted(folders.keys())
    assert list(storage.task_ids) == []

    # make sure everything matches the structure built by the fixture
    for subj_id, tasknames in folders.items():
        storage.subject_id = subj_id
        assert list(storage.task_ids) == tasknames

    # try a non-existing subject
    storage.subject_id = 'other_subject'
    assert list(storage.task_ids) == []

    # create a new task
    storage.create_task('task1', ['attr1', 'attr2'])
    assert os.path.exists(os.path.join(root, storage.subject_id, 'task1'))
    assert list(storage.task_ids) == ['task1']
    # ensure you can't overwrite existing task
    with pytest.raises(ValueError):
        storage.create_task('task1', [])

    # require an existing task
    storage.require_task('task1')
    # fail if you require a non-existing task
    with pytest.raises(ValueError):
        storage.require_task('task2')


def test_task_writer(tmpdirpath):
    # simple writer with a couple columns and no arrays
    print(tmpdirpath)
    cols = ['block', 'trial', 'attr']
    data = [[0, 0, 0.5], [0, 1, 0.2]]

    # fill in data for task1
    task_root = os.path.join(tmpdirpath, 'task1')
    os.makedirs(task_root)
    writer = TaskWriter(task_root, cols)

    writer.write(data[0])
    writer.write(data[1])

    fdata = pandas.read_csv(os.path.join(task_root, 'trials.csv'))
    assert fdata.equals(pandas.DataFrame(data, columns=cols))

    # writer with some array data
    cols = ['trial', 'attr']
    trials = [[0, 'a'], [1, 'b']]

    task_root = os.path.join(tmpdirpath, 'task2')
    os.makedirs(task_root)
    writer = TaskWriter(task_root, cols, array_names=['array1', 'array2'])

    writer.arrays['array1'].stack(numpy.array([0, 1, 2]))
    writer.arrays['array2'].stack(numpy.array([0.0, 0.1, 0.2]))
    writer.write(trials[0])

    writer.arrays['array1'].stack(numpy.array([3, 4, 5]))
    writer.arrays['array2'].stack(numpy.array([0.3, 0.4, 0.5]))
    writer.arrays['array2'].stack(numpy.array([0.6, 0.7, 0.8]))
    writer.write(trials[1])

    arrdata = read_hdf5(os.path.join(task_root, 'array2.hdf5'), dataset='1')
    numpy.testing.assert_array_equal(
        arrdata,
        numpy.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.8]))


def test_array_writer(tmpdirpath):
    fn = 'arrays.hdf5'
    fp = os.path.join(tmpdirpath, fn)
    print(tmpdirpath)

    x_expected = numpy.array([[0, 1, 2], [3, 4, 5]])

    # horizontal stacking of a 1-D array
    writer = ArrayWriter(fp)

    assert fn not in os.listdir(tmpdirpath)
    writer.stack(x_expected[0])
    writer.stack(x_expected[1])
    writer.write('0')
    assert fn in os.listdir(tmpdirpath)
    data = read_hdf5(fp, dataset='0')
    numpy.testing.assert_array_equal(x_expected.reshape(1, -1).squeeze(), data)

    # vertical stacking of 1-D arrays to get a 2-D array
    writer = ArrayWriter(fp, orientation='vertical')
    writer.stack(numpy.array([0, 1, 2]))
    writer.stack(numpy.array([3, 4, 5]))
    writer.write('1')

    data = read_hdf5(fp, dataset='1')
    numpy.testing.assert_array_equal(x_expected, data)


def test_trial_writer(tmpdirpath):
    fn = 'trials.csv'
    fp = os.path.join(tmpdirpath, fn)

    cols = ['a', 'b', 'c']

    writer = TrialWriter(fp, cols)

    # test array data
    data = [[1, 2, 3.0], [4, 5, 6.0]]
    writer.write(data[0])
    assert writer.data.equals(pandas.DataFrame([data[0]], columns=cols))
    writer.write(data[1])
    assert writer.data.equals(pandas.DataFrame(data, columns=cols))

    # file actually contains the data
    assert pandas.read_csv(fp).equals(pandas.DataFrame(data, columns=cols))

    # test dict data
    data = {'b': 4, 'a': 2, 'c': 4.2}
    writer = TrialWriter(fp, cols)
    writer.write(data)
    assert writer.data.equals(pandas.DataFrame(data, columns=cols, index=[0]))


def test_hdf5_read_write(tmpdirpath):
    fp = os.path.join(tmpdirpath, 'file.hdf5')

    x_expected = numpy.array([[0.1, 2.1, 4.1], [2.1, 4.2, 2.1]])

    write_hdf5(fp, x_expected)
    x = read_hdf5(fp)
    numpy.testing.assert_array_equal(x_expected, x)

    write_hdf5(fp, x_expected, dataset='somedata')
    x = read_hdf5(fp, dataset='somedata')
    numpy.testing.assert_array_equal(x_expected, x)


def test_storage_to_zip(tmpdirpath):
    # make a dataset root under a subfolder
    p = os.path.join(tmpdirpath, 'datasets', 'dataset01')
    os.makedirs(p)
    with open(os.path.join(p, 'file.txt'), 'w') as f:
        f.write("hello")

    outfile = os.path.join(tmpdirpath, 'datasets', 'dataset01.zip')
    zipfile = storage_to_zip(p)
    assert zipfile == outfile
    assert os.path.isfile(outfile)

    outfile = os.path.join(tmpdirpath, 'dataset01_relocated.zip')
    zipfile = storage_to_zip(p, outfile=outfile)
    assert zipfile == outfile
    assert os.path.isfile(outfile)
