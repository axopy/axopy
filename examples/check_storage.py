from axopy import storage


if __name__ == '__main__':
    # instantiate the storage file
    db = storage.ExperimentDatabase('file.hdf5', 'w')

    tgrp = db.create_trial(pid='p0', task='Training', session='a', trial='0')
    tgrp.create_dataset('dat', data=[1, 2, 3])
    #pgrp = db.create_participant('p0')
    #tgrp = pgrp.create_task('Training')

    # create a task group and wrap it in the desired interface
    #taskdb = db.create_task('p0', 'Training')

    ## generate some trials
    #taskdb.create_session('arm-1')
    #taskdb.create_trial('0', data=[1, 2, 3])
    #taskdb.create_trial('1', data=[4, 5, 6])

    ##print(list((taskdb.get_trial('0').attrs.items())))
    #print('0' in taskdb.get_session('arm-1'))
    #db.close()


    #db = storage.ExperimentDatabase('file.hdf5', 'r')

    #taskdb = storage.TaskGroup(db.get_task('p0', 'Training'))
    #print(taskdb.get_trial('0').attrs)
