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
        # filename_format determines how to save/load the data in DB


    def prepare_reciever(self):
        self.model = some_machine_learning_alg(data)

    def emg_data_reciever(self,emgdata):
        # upon emg data recieved, release gesture output signal
        issue_gesture_output(self.model(emgdata)) 

class TrainGestureModel(BaseTask, RequiredParticipantMixin):
    # require collected gesture training data (assume 1 trainign data)
    # maybe don't need RequiredParticipantMixin?



class RealTimeControlToTarget(BaseTask, RequiredParticipantMixin):
    # require traingesturemodel completed. maybe don't need mixin?
    
    # blocks are just defined in class? then when instantiated, fill in data
    daq = DaqBlock()
    emgfilter = EMGFilterBlock(listen_to=daq)
    gesture = GesturePredictionBlock(listen_to=emgfilter)
    gesture_to_velocity = GestureToVelocityBlock(listen_to=gesture)
    velocity_controller = VelocityCntrollerBlock(listen_to=gesture_to_velocity)
    cursor_target = CursorTargetBlock(listen_to=())


if __name__ == '__main__':
    # a daq block
    daq = EmulatedDaq(rate=1000, num_channels=2, read_size=100)
    gesture_block = GestureModel(filename_format='')

    # for this example use memory-backed store instead of file
    # a file storage block
    db = ExperimentDatabase('file.hdf5', driver='core', backing_store=False)

    with application(daq, db) as app:
        app.install_task(SelectParticipant)
        app.install_task(Oscilloscope(daqblock=daq))
        app.install_task(CollectGestureTrainngData(repeat_gesture=2))
        app.install_task(RealTimeControlToTarget(dof=2,timout=10,max_distance=30,))
        