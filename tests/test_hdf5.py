import pytest
from axopy.streams import hdf5


@pytest.fixture
def blankh5(tmpdir):
    """Blank `HDF5Storage` object with write privileges."""
    fn = tmpdir.join('file.h5')
    db = hdf5.HDF5Storage(str(fn))
    return db


def test_new_participant(blankh5):
    grp = blankh5.require_participant('p0')
    assert grp.name == '/p0'
    assert blankh5.current_participant == 'p0'


def test_new_task(blankh5):
    # ensure exception is raised if no participant provided and one hasn't been
    # added yet
    with pytest.raises(ValueError):
        blankh5.require_task('sometask')

    # create a participant, then create a task with implicit pid
    blankh5.require_participant('p0')
    grp = blankh5.require_task('sometask')
    assert grp.name == '/p0/sometask'

    # provide pid in require_task
    grp = blankh5.require_task('sometask', participant='p1')
    assert grp.name == '/p1/sometask'


def test_new_run(blankh5):
    # try creating a run with no participant or task selected/provided
    with pytest.raises(ValueError):
        blankh5.require_run('run1')

    # select a particpiant but no task
    with pytest.raises(ValueError):
        blankh5.require_run('run1', participant='p0')

        blankh5.require_participant('p0')
        blankh5.require_run('run1')

    # create participant/task and then a run
    blankh5.require_task('sometask', participant='p0')
    grp = blankh5.require_run('run1')
    assert grp.name == '/p0/sometask/run1'

    # all in one go
    grp = blankh5.require_run('run1', task='sometask', participant='p1')
    assert grp.name == '/p1/sometask/run1'


def test_new_trial(blankh5):
    with pytest.raises(ValueError):
        blankh5.require_trial('trial1')

    blankh5.require_run('run1', task='sometask', participant='p0')
    grp = blankh5.require_trial('trial1')
    assert grp.name == '/p0/sometask/run1/trial1'
