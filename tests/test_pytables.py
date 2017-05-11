import pytest
import tables
import numpy

from axopy.streams.pytables import PyTablesSink

@pytest.fixture
def newfile(tmpdir):
    """Blank PyTables `File` object with write privileges in a tmpdir."""
    fn = tmpdir.join('file.h5')
    f = tables.open_file(str(fn), 'w')
    yield f
    f.close()


def test_sink(newfile):
    # mixture of regular Python and numpy dtypes
    data_format = {
        'timestamp': float,
        'trialnum': int,
        'float32': numpy.float32,
        'array': numpy.dtype((numpy.float32, (2,)))
    }

    sink = PyTablesSink(newfile, 'mytable', data_format)
    # ensure a table was created upon creation of the sink
    table = newfile.get_node('/', 'mytable')
    assert isinstance(table, tables.Table)

    # write some data and check that rows are added to the table
    sink(4.2, 1, 63.2, numpy.array([4., 5.], dtype=numpy.float32))
    sink(5.3, 2, 92.1, numpy.array([6., 7.], dtype=numpy.float32))
    assert table.nrows == 2
