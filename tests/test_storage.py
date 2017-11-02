import pytest
import os
import numpy
from axopy.storage import (Storage, TaskWriter, ArrayWriter, read_hdf5,
                           write_hdf5, storage_to_zip)


@pytest.fixture(scope='module')
def storage_filestruct(tmpdir_factory):
    """Generates the following data filestructure::

        data/
            p0/
                task1/
                task2/
            p1/
                task1/
            p2/

    """
    root = str(tmpdir_factory.mktemp('data'))

    folders = {'p0': ['task1', 'task2'], 'p1': ['task1'], 'p2': []}

    for subj_id, tasknames in folders.items():
        os.makedirs(os.path.join(root, subj_id))
        for name in tasknames:
            os.makedirs(os.path.join(root, subj_id, name))

    return root, folders


def test_storage_directories(storage_filestruct):
    """Test that Storage can find and create the right directories."""
    root, folders = storage_filestruct

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


def test_task_writer(storage_filestruct):
    root, folders = storage_filestruct

    task_id = 'some_task'
    task_root = os.path.join(root, list(folders)[0])

    # simple writer with one column and no arrays
    #writer = TaskWriter(task_root, task_id, ['trial'])

    #writer.start_trial()
    #writer.write_trial(0)

    #with pytest.raises(Exception):
    #    writer.write_trial(0)

    #writer.start_trial()
    #writer.write_trial(1)

    ## TODO check that the file at task_root/trial_data.csv is correct

    #writer.finish()

    ## writer with a column and an array
    ## note ok to manually create a TaskWriter for data that already exists
    #writer = TaskWriter(task_root, task_id, ['block', 'trial'],
    #                    array_names=['arr'])

    #writer.start_trial()
    #writer.write_trial(0, 0)
    #writer.arrays['arr'].stack(numpy.arange(10))
    #writer.arrays['arr'].stack(numpy.arange(10))

    ## TODO assert data at task_root/arr/0.hdf5 is correct


def test_array_writer(tmpdir):
    fn = 'arrays.hdf5'
    root = str(tmpdir.dirpath())
    fp = os.path.join(root, fn)

    x_expected = numpy.array([[0, 1, 2], [3, 4, 5]])

    # horizontal stacking of a 1-D array
    writer = ArrayWriter(fp)

    assert fn not in os.listdir(root)
    writer.stack(x_expected[0])
    writer.stack(x_expected[1])
    writer.write('0')
    assert fn in os.listdir(root)
    data = read_hdf5(fp, dataset='0')
    numpy.testing.assert_array_equal(x_expected.reshape(1, -1).squeeze(), data)

    # vertical stacking of 1-D arrays to get a 2-D array
    writer = ArrayWriter(fp, orientation='vertical')
    writer.stack(numpy.array([0, 1, 2]))
    writer.stack(numpy.array([3, 4, 5]))
    writer.write('1')

    data = read_hdf5(fp, dataset='1')
    numpy.testing.assert_array_equal(x_expected, data)


def test_hdf5_read_write(tmpdir):
    fp = os.path.join(str(tmpdir.dirpath()), 'file.hdf5')

    x_expected = numpy.array([[0.1, 2.1, 4.1], [2.1, 4.2, 2.1]])

    write_hdf5(fp, x_expected)
    x = read_hdf5(fp)
    numpy.testing.assert_array_equal(x_expected, x)

    write_hdf5(fp, x_expected, dataset='somedata')
    x = read_hdf5(fp, dataset='somedata')
    numpy.testing.assert_array_equal(x_expected, x)


def test_storage_to_zip(tmpdir):
    # make a dataset root under a subfolder
    p = os.path.join(str(tmpdir.dirpath()), 'datasets', 'dataset01')
    os.makedirs(p)
    with open(os.path.join(p, 'file.txt'), 'w') as f:
        f.write("hello")

    outfile = os.path.join(str(tmpdir.dirpath()), 'datasets', 'dataset01.zip')
    zipfile = storage_to_zip(p)
    assert zipfile == outfile
    assert os.path.isfile(outfile)

    outfile = os.path.join(str(tmpdir.dirpath()), 'dataset01_relocated.zip')
    zipfile = storage_to_zip(p, outfile=outfile)
    assert zipfile == outfile
    assert os.path.isfile(outfile)
