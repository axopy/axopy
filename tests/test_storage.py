import pytest
import numpy
from axopy.storage import TaskStorage


def test_task_storage(tmpdir):
    s = TaskStorage('some_task', '1', root=tmpdir.dirpath(),
                    columns=['trial', 'param1', 'param2'])
    arr = s.create_array('position')
    arr.add(numpy.random.randn(2, 10))
    arr.add(numpy.random.randn(2, 10))
    assert arr.buffer.data.shape == (2, 20)
    s.write_trial(None)
