from axopy import storage
import numpy as np


class ExampleTask(object):

    def run(self, storage):
        storage.create_session('session1')
        for trial_num in range(5):
            trial = storage.create_trial('trial{}'.format(trial_num))
            trial['duration'] = 3.2
            trial['success'] = True
            trial.create_dataset('rec', np.random.rand(10), attrs={'fs': 1})


def setup_storage():
    db = storage.ExperimentDatabase('file.hdf5', 'w')
    #db.install_task('ExampleTask', ExampleTrialStorage)
    return db


if __name__ == '__main__':
    db = setup_storage()
    db.require_participant('p0')

    grp = db.require_task('p0', 'ExampleTask')
    task = ExampleTask()
    task.run(grp)
