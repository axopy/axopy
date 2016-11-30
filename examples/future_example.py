"""
This is a pseudo-code-ish example for me to figure out how making a custom
experiment should look once the library is more complete.
"""


class TrainTask(ExperimentTask):

    def __init__(self, task_storage):
        self.task_storage = task_storage


class TACTask(ExperimentTask):

    def __init__(self, pipeline, task_storage, train_storage):
        self.pipeline = pipeline
        self.task_storage = task_storage
        self.train_storage = train_storage

    def start(self):
        data = self.train_storage.collect_sessions(self._subject,
                                                   self._selected_sessions)
        self.pipeline.named_blocks('classifier').fit(*data)


def setup_oscilloscope(daq):
    pipeline = Pipeline(
        [
            daq,
            FeatureExtractor([
                ('rms', RMS()),
                ('ssc', SSC())
            ]),
            Ensure2D(),
            Windower(100)
        ]
    )

    return Oscilloscope(pipeline)


def setup_train_task(daq, task_storage):
    pipeline = Pipeline([daq])
    return TrainTask(pipeline, task_storage)


def setup_tac_task(daq, task_storage, train_storage):
    pipeline = Pipeline(
        [
            daq,
            FeatureExtractor([
                ('rms', RMS()),
                ('ssc', SSC()),
                ('wl', WL())
            ]),
            Estimator(LinearDiscriminantAnalysis(), name='classifier'),
            DBVRController({0: 'rest', 1: 'open-hand', 2: 'close-hand'})
        ]
    )

    return TACTask(pipeline, task_storage, train_storage)


if __name__ == '__main__':
    daq = EmulatedDaq(rate=1000, num_channels=2, read_size=100)

    db = ExperimentDatabase('file.hdf5', 'a')
    train_group = db.require_task('TrainTask')
    tac_group = db.require_task('TACTask')

    with application(daq, db) as app:
        app.install_task(setup_oscilloscope(daq))
        app.install_task(setup_train_task(daq, train_group))
        app.install_task(setup_tac_task(daq, tac_group, train_group))
