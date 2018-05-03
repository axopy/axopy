import pytest
import os
import numpy
import pandas
from axopy.design import Design
from axopy.storage import (Storage, TaskWriter, TrialWriter, read_hdf5,
                           write_hdf5, storage_to_zip, makedirs)


@pytest.fixture(scope='function')
def tmpdirpath(tmpdir):
    """Convenience fixture to get the path to a temporary directory."""
    return str(tmpdir.dirpath())


def test_storage(tmpdirpath):
    """Integration test for regular storage usage with task design."""
    # usually done by task manager
    storage = Storage(root=tmpdirpath)
    storage.subject_id = 'p0'

    writer = storage.create_task('task1')
    # task design and writing
    d = Design()
    b = d.add_block()

    t = b.add_trial(attrs={'trial': 0, 'label': 'a'})
    t.add_array('data', data=numpy.zeros(5))
    writer.write(t)

    t = b.add_trial(attrs={'trial': 1, 'label': 'b'})
    t.add_array('data', data=numpy.zeros(3))
    writer.write(t)

    writer.pickle([1, 2, 3], 'somelist')

    # task reading
    reader = storage.require_task('task1')
    assert len(reader.trials) == 2
    arrays = reader.iterarray('data')
    assert next(arrays).shape == (5,)
    assert next(arrays).shape == (3,)

    assert reader.pickle('somelist') == [1, 2, 3]


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
    storage.create_task('task1')
    assert os.path.exists(os.path.join(root, storage.subject_id, 'task1'))
    assert list(storage.task_ids) == ['task1']
    # ensure you can't overwrite existing task
    with pytest.raises(ValueError):
        storage.create_task('task1')

    # require an existing task
    storage.require_task('task1')
    # fail if you require a non-existing task
    with pytest.raises(ValueError):
        storage.require_task('task2')


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


def test_makedirs(tmpdir):
    path = os.path.join(str(tmpdir.dirpath()), 'subdir', 'subsubdir')

    # regular usage
    makedirs(path)
    assert os.path.exists(path)

    # fail if path already exists
    with pytest.raises(OSError):
        makedirs(path)

    # succeed if path exists but that's ok
    makedirs(path, exist_ok=True)
