import h5py
import datetime


class HDF5Node:
    """Individual destination/source that a task can stream to/from.

    An example would be a task where you want to store an array of raw input
    data along with some event data for each trial. Each of those distinct
    "arrays" would get their own stream.
    """
    pass


# TODO: add **attrs to each of the `require_<level>` methods
# TODO: make `current_<level>` attributes iterable somehow
# TODO: consider making `current_<level>` attrs properties with side effects

class HDF5Storage(h5py.File):
    """Top-level storage unit for an experiment backed by HDF5.

    An `HDF5Storage` object can be used for both creating an experiment dataset
    and reading an existing one.

    `HDF5Storage` maintains a set of attributes for keeping track of the
    current location in the dataset hierarchy for convenience. These should
    always be in agreement such that you could combine them together to form
    the path to the current trial.

    Attributes
    ----------
    current_participant : str
        ID of the currently selected participant.
    current_task : str
        Name of the currently selected task.
    current_run : str
        Name of the currently selected run.
    current_trial : str
        Name of the currently selected trial.
    """

    def __init__(self, *args, **kwargs):
        super(HDF5Storage, self).__init__(*args, **kwargs)

        self.current_participant = None
        self.current_task = None
        self.current_run = None
        self.current_trial = None

    def require_participant(self, participant):
        """Retrieve the group in the file holding all of the participant's data.

        If the participant is not already registered in the file, a group is
        created (assuming file mode includes writing). This also sets the
        currently selected participant.

        Parameters
        ----------
        participant : str
            Participant identifier.
        """
        self.current_participant = participant
        return self.require_group(participant)

    def require_task(self, task, participant=None):
        """Retrieves a task storage group for a participant.

        If the task group is not already registered in the file, a group is
        created (assuming file mode includes writing). This also sets the
        currently selected task as well as the current participant (if
        provided).

        Parameters
        ----------
        task : str
            Name of the task.
        participant : str, optional
            Participant ID. If not provided, the currently selected participant
            ID is used.
        """
        participant = self._check_current('participant', participant)
        self.current_task = task
        grp = self.require_participant(participant)
        return grp.require_group(task)

    def require_run(self, run, task=None, participant=None):
        """Retrieves a run storage group for a task.

        If the run group is not already registered in the file, a group is
        created (assuming file mode includes writing). This also sets the
        currently selected run, task, and participant.

        Parameters
        ----------
        run : str
            Name of the run to create.
        task : str, optional
            Name of the task. If not provided, the currently selected task is
            used.
        participant : str, optional
            Participant ID. If not provided, the currently selected participant
            ID is used.
        """
        task = self._check_current('task', task)
        self.current_run = run
        grp = self.require_task(task, participant=participant)
        return grp.require_group(run)

    def require_trial(self, trial, run=None, task=None, participant=None):
        """Retrieves a trial storage group for a run.

        If the trial group is not already registered in the file, a group is
        created (assuming file mode includes writing). This also sets the
        currently selected trial, run, task, and participant.

        Parameters
        ----------
        trial : str
            Name of the trial to create.
        run : str
            Name of the run to create.
        task : str, optional
            Name of the task. If not provided, the currently selected task is
            used.
        participant : str, optional
            Participant ID. If not provided, the currently selected participant
            ID is used.
        """
        run = self._check_current('run', run)
        self.current_trial = trial
        grp = self.require_run(run, task=task, participant=participant)
        return grp.require_group(trial)

    def _check_current(self, level, val):
        """Ensures either the current value of a level in the hierarchy is set
        or provided.
        """
        self_val = getattr(self, 'current_{}'.format(level))
        if val is None:
            if self_val is None:
                raise ValueError("Must provide a {} since none has been"
                                 " selected".format(level))
            val = self_val
        return val

    def get_participants(self):
        return list(self.keys())


def dt():
    dt = datetime.datetime.now()
    return str(dt.date()), str(dt.time())
