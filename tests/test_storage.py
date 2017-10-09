import pytest
import os
import numpy
from axopy.storage import TaskStorage, storage_to_zip


#def test_task_storage(tmpdir):
#    s = TaskStorage('some_task', '1', root=tmpdir.dirpath(),
#                    columns=['trial', 'param1', 'param2'])
#    arr1 = s.new_array('array1')
#    arr2 = s.new_array('array2', orientation='vertical')
#
#    arr1.stack(numpy.random.randn(2, 10))
#    arr1.stack(numpy.random.randn(2, 10))
#    assert arr1.data.shape == (2, 20)
#
#    arr2.stack(numpy.random.randn(2, 10))
#    arr2.stack(numpy.random.randn(2, 10))
#    assert arr2.data.shape == (4, 10)
#
#    s.write_trial(None)


#class SomeTask(Task):
#
#    def __init__(self, name, dep_task):
#        self.name = name
#        self.in_task_name = dep_task
#
#    def prepare_input_device(self, device):
#        self.device.updated.connect(self.update)
#
#    def prepare_storage(self, storage):
#        """Storage has already been created with subject ID and root path."""
#        self._load_data(storage.find_task(self.in_task_name))
#
#        s = storage.new_task(self.name, )
#        self.emg_storage = s.new_array('emg')
#        self.position_storage = s.new_array('position')
#
#    def _load_data(self, task_storage):
#        """Load data from a previous task."""
#        # task_storage.trials is a pandas DataFrame
#        # in this case, we're acting like a processing task generated x/y
#        # positions paired with a set of features from the input signals
#        data = task_storage.trials
#        pos_cols = ['x', 'y']
#        positions = data[pos_cols].values
#        features = data.drop(pos_cols, axis=1).values
#        self.pipeline.named_blocks['mapper'].fit(features, positions)
#
#    def update(self, data):
#        pos = self.pipeline.process(data)
#        self.cursor.position = pos
#
#
#def test_storage_write(tmpdir):
#    s = Storage('data')
#    s.add_task('mapping')
#    s.add_task('')
#    s.add_task('cursor_practice')
#    s.add_task('adaptation')
#    s('hello', outfile='hellono')


def test_storage_to_zip(tmpdir):
    # make a dataset root under a subfolder
    p = os.path.join(tmpdir.dirpath(), 'datasets', 'dataset01')
    os.makedirs(p)
    with open(os.path.join(p, 'file.txt'), 'w') as f:
        f.write("hello")

    outfile = os.path.join(tmpdir.dirpath(), 'datasets', 'dataset01.zip')
    zipfile = storage_to_zip(p)
    assert zipfile == outfile
    assert os.path.isfile(outfile)

    outfile = os.path.join(tmpdir.dirpath(), 'dataset01_relocated.zip')
    zipfile = storage_to_zip(p, outfile=outfile)
    assert zipfile == outfile
    assert os.path.isfile(outfile)
