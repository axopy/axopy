
class DataProcessingBlock(Block):
    classifier = gesture_class
    joint_velocity = emitter()

    def recieve_raw_emg(self,data):
        gesture, intensity = classifier(data)
        joint_velocity = function(gesture,intensity)

        self.send_joint_velocity(joint_velocity)
        self.send_gesture(gesture)

class TimerBlock(Block):
    def recieve_end_trial(self,data):
        self.send_cend_trial_time()


class TacTestTask(Task):
    Storage = HD5StorageDevice

    VRepClient = VRepClientDevice
    
    VRepClient.joint_angles.emit_to(Storage)
    VRepClient.in_target.emit_to(TrialIterator)
    

    EMG = DaqDevice
    EMG.raw_data.emit_to(Storage)

    TrialExperimentTimer = TimerBlock(timeout=10)
    TrialExperimentTimer.timeout.emit_to(end_trial)
    TrialExperimentTimer.end_trial_time.emit_to(Storage)

    DataProcessor = DataProcessingBlock

    EMG.raw_data.emit_to(DataProcessor)
    DataProcessor.joint_velocity.emit_to(VRepClient)
    DataProcessor.gesture.emit_to(Storage)
    


    def prepare_task(self,):
        dataset = QtFile(...) # select the dataset
        classifier = get_classifier_from(data,self.classifier_args)
        # any blocking 
        super(self,TacTestTask).prepare_task(*args,**kwargs)

    def prepare_trial(self,trial_data):
        VRepClient.set_initial_angles(trial_data[initial_angles])
        VRepClient.set_target_angles(trial_data[target_angles])
        super(self,TacTestTask).prepare_task(*args,**kwargs)

class KennysExperiment(KennysExperiment):
    Block1 = TacTestTask([ """ list of trials """], classifier_args={'active_dof': [1,2,3,4]})
    Block2 = TacTestTask([ """ list of trials """], classifier_args={'dof': [1,2,3,4,7,8]})


def __name__=='__main__':
    KennysExperiment().run()
