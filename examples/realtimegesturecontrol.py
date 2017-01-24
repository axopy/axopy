from PyQt5 import QtWidgets, QtGui
from numpy import zeros

from axopy.application import (application, ExperimentTask,
                               DataVisualizationTask)
from axopy.storage import ExperimentDatabase, SimpleTrialStorage
from axopy.daq import EmulatedDaq
from axopy.tasks import (BaseTask, RequiredParticipantMixin, Oscilloscope, 
                         SelectParticipant)
from axopy.blocks import (BaseBlock, CursorTarget, )
from axopy.signals import Signals

"""
pseudo-code to implement real-time gesture control

"""

class CollectGestureTrainngData(BaseTask, RequiredParticipantMixin):
    pass

class GesturePredictor(BaseBlock):
    data = db.get(r'//')
    
    def __init__(self,filename_Format='%%pid%%_gesture_data'):
        # filename_format determines how to create new rows in the DB or
        # files in the filesystem 


    def prepare_reciever(self):
        self.model = some_machine_learning_alg(data)

    def emg_data_reciever(self,emgdata):
        # upon emg data recieved, release gesture output signal
        issue_gesture_output(self.model(emgdata)) 

class TrainGestureModel(BaseTask, RequiredParticipantMixin):
    # require collected gesture training data (assume 1 trainign data)
    # maybe don't need RequiredParticipantMixin?



class RealTimeControlToTarget(BaseTask, RequiredParticipantMixin):
    # require traingesturemodel completed. maybe don't need requiredparticipant?
    
    # blocks are just defined in class? then when instantiated, fill in data
    daq = DaqBlock() 
    # either get the reference to control the daq as an __init__ arg OR
    # when this class is defined by __new__, figure out my parent and get the
    # daq from them

    # QT signal/slot-like definitions, which are actually plugged in later
    emgfilter = EMGFilterBlock(listen_to=daq)
    gesture = GesturePredictionBlock(listen_to=emgfilter)
    gesture_to_velocity = GestureToVelocityBlock(gesture_input=gesture)

    velocity_controller = VelocityCntrollerBlock(
        velocity_input=gesture_to_velocity)
    cursor_target = CursorTargetBlock(cursor_input=velocity_controller,
        target_position=None)

    def prepare_trial(self):
        trial_parameters = self.trial_parameters.next() 
        # this should actually be done in a higher level


        cursor_target.set_target_xy(trial_parameters['target_pos'])

        # other things automatically listen to a prepare_trial signal?

    def cleanup_trial(self):
        db.save_data(trial_parameters['filename'], cursor_target.time_to_target)


class QTDisplayRecordings(Task):
    file_select = QTFileDialogBlock(r'a\specification\for\what\files\are\eligible')
    loaded_data = FileStream.load(file_select)
   display = QTPlotter(loaded_data)

   


class RealTimeControlExperiment(QTExperiment):
    # define persistent-ish classes, which somehow 
    db = ExperimentDatabase('file.hdf5', driver='core', backing_store=False)
    daq = EmulatedDaq(rate=1000, num_channels=2, read_size=100)
    gesture_block = GestureModel(filename_format='')

    tasks = [
        SelectParticipant,
        Oscilloscope(daqblock=daq),
        CollectGestureTrainngData(repeat_gesture=2),
        RealTimeControlToTarget(dof=2,timout=10,max_distance=30,)
    ]


if __name__ == '__main__':
    RealTimeControlExperiment.run()