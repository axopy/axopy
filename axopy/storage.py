"""
Basic data storage framework backed by h5py.
"""

import h5py
import datetime


class ExperimentDatabase(h5py.File):
    """Top-level storage unit for an experiment backed by HDF5.
    """

    def create_participant(self, pid):
        return self.create_group(participant_path(pid))

    def get_participant(self, pid):
        return self.get(participant_path(pid))

    def require_participant(self, pid):
        return self.require_group(participant_path(pid))

    def create_task(self, pid, name):
        return self.create_group(task_path(pid, name))

    def get_task(self, pid, name):
        return self.get(task_path(pid, name))

    def require_task(self, pid, name):
        return self.require_group(task_path(pid, name))

    def get_participants(self):
        return list(self.keys())


class _BaseTaskStorage(object):

    def __init__(self, group):
        self.group = group
        self.current_session = None

    def get_session(self, name):
        session = self.group.get(name)
        self.current_session = session
        return self.current_session

    def create_session(self, name):
        session = self.group.create_group(name)
        session.attrs['date'] = dt()[0]
        self.current_session = session
        return self.current_session

    def _get_session(self, session=None):
        if session is None:
            session = self.current_session

        if isinstance(session, str):
            session = self.get_session(session)

        return session


class SimpleTrialStorage(_BaseTaskStorage):
    """A simple storage scheme suitable for many tasks.

    Each session gets its own group, and each trial of the session consists of
    a single dataset (a single homogeneous array). This storage scheme is
    suitable for tasks involving raw data capture or tasks meant for simple
    processing of raw data (e.g. signal conditioning) or feature computation.

    This class can be used both for saving new data (create mode) or loading
    existing data (get mode). To use create mode, pass a Group object that
    create yourself. To use get mode, pass a Group object that already exists
    in storage.

    Parameters
    ----------
    group : h5py.Group
        The group belonging to the task.

    Attributes
    ----------
    current_session: h5py.Group
        The subgroup of the task group representing the current session for the
        task. In create mode, the most recently created session is used. In get
        mode, the most recently retrieved session is used.
    """

    def create_trial(self, name, session=None, shape=None, dtype=None,
                     data=None):
        """Create a trial dataset.

        Parameters
        ----------
        name : str
            Name of the trial to create.
        session : h5py.Group or str, optional
            The session to create the trial in. If ``None`` (default), the
            task's `current_trial` is used. Can be either the Group object
            corresponding to the session or the name.
        shape : tuple, optional
            The shape of the dataset array. One of `shape` or `data` must be
            provided.
        dtype : str, optional
            Data type for the array.
        data : array, optional
            The data for the trial.
        """
        session = self._get_session(session)
        trial = session.create_dataset(name, shape=shape, dtype=dtype,
                                       data=data)
        trial.attrs['time'] = dt()[1]
        return trial

    def get_trial(self, name, session=None):
        session = self._get_session(session)
        trial = session.get(name)
        return trial


def participant_path(pid):
    return '{}'.format(pid)


def task_path(pid, experiment_id):
    return '{}/{}'.format(participant_path(pid), experiment_id)


def dt():
    dt = datetime.datetime.now()
    return str(dt.date()), str(dt.time())
