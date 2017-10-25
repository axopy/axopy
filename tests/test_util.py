import pytest
import os
from axopy.util import makedirs


def test_makedirs(tmpdir):
    path = os.path.join(tmpdir.dirpath(), 'subdir', 'subsubdir')

    # regular usage
    makedirs(path)
    assert os.path.exists(path)

    # fail if path already exists
    with pytest.raises(OSError):
        makedirs(path)

    # succeed if path exists but that's ok
    makedirs(path, exist_ok=True)
