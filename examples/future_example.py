"""
This is a pseudo-code-ish example for me to figure out how making a custom
experiment should look once the library is more complete.
"""

gesture_mapping = {
    0: 'rest',
    1: 'open-hand',
    2: 'close-hand'
}


# 1. define custom tasks
#   - each custom task should be in a separate module or maybe all custom
#     custom tasks could be put in a single module `tasks.py`


class TACTask(ExperimentTask):

    def __init__(self, pipeline, task_storage, train_storage):
        self.pipeline = pipeline
        self.task_storage = task_storage
        self.train_storage = train_storage

    def start(self):
        data = self.train_storage.collect_sessions(self._subject,
                                                   self._selected_sessions)
        self.pipeline.named_blocks('classifier').fit(*data)


# 2. write functions to set up each task
#   - task implementations should be fairly general (e.g. a specific pipeline
#     isn't enforced), so some things need to be set up to be passed in to
#     the tasks __init__
#   - having a separate function to do the setup allows `main()` to look like
#     a high level overview of the task


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
    def img_path(name):
        return pkg_resources.resource_filename(
            os.path.join(__name__, 'images', name+'.png'))

    pipeline = Pipeline([daq])
    imgs = [l: img_path(n) for l, n in gesture_mapping.items()]

    return ImageTrainingTask(pipeline, images=imgs, task_storage=task_storage)


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


# 3. write an entry point
#   - set up storage and a data source
#   - initialize the main application
#   - set up and install the tasks


def main():
    daq = EmulatedDaq(rate=1000, num_channels=2, read_size=100)

    db = ExperimentDatabase('file.hdf5', 'a')
    train_group = db.require_task('TrainTask')
    tac_group = db.require_task('TACTask')

    with application(daq, db) as app:
        app.install_task(setup_oscilloscope(daq))
        app.install_task(setup_train_task(daq, train_group))
        app.install_task(setup_tac_task(daq, tac_group, train_group))


if __name__ == '__main__':
    main()
