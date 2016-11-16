"""
Basic data storage framework backed by h5py.
"""

import h5py
import datetime


class ExperimentDatabase(h5py.File):
    """Top-level storage unit for an experiment backed by HDF5.
    """

    def create_participant(self, pid):
        """Create a group in the file to hold all of a participant's data.

        Parameters
        ----------
        pid : str
            Participant identifier. Used as the group name.
        """
        return self.create_group(participant_path(pid))

    def get_participant(self, pid):
        """Retrive the group in the file holding all of a participant's data.

        Parameters
        ----------
        pid : str
            Participant identifier.
        """
        return self.get(participant_path(pid))

    def require_participant(self, pid):
        """Retrieve the group in the file holding all of the participant's data.

        If the participant is not already registered in the file, a group is
        created.

        Parameters
        ----------
        pid : str
            Participant identifier.
        """
        return self.require_group(participant_path(pid))

    def create_task(self, pid, name):
        """Instantiate a task for a participant.

        If the task (by name) has been installed into the experiment storage
        file, an object of that task storage class is returned. Otherwise, a
        :class:`BaseTaskStorage` object is returned.

        Parameters
        ----------
        pid : str
            Participant ID to creae the task for.
        name : str
            Name of the task.
        """
        return TaskStorage(self.create_group(task_path(pid, name)))

    def get_task(self, pid, name):
        """Retrieves a task storage group for a participant.

        If the task (by name) has been installed into the experiment storage
        file, an object of that task storage class is returned. Otherwise, a
        :class:`BaseTaskStorage` object is returned.

        Parameters
        ----------
        pid : str
            Participant ID to creae the task for.
        name : str
            Name of the task.
        """
        return TaskStorage(self.get(task_path(pid, name)))

    def require_task(self, pid, name):
        """Retrieves a task storage group for a participant.

        If the task group is not already registered in the file, a group is
        created.

        If the task (by name) has been installed into the experiment storage
        file, an object of that task storage class is returned. Otherwise, a
        :class:`BaseTaskStorage` object is returned.

        Parameters
        ----------
        pid : str
            Participant ID to creae the task for.
        name : str
            Name of the task.
        """
        return TaskStorage(self.require_group(task_path(pid, name)))

    def get_participants(self):
        return list(self.keys())



class TaskStorage(object):
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

    def __init__(self, group, trial_cls=None):
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

    def create_trial(self, name, session=None):
        session = self._get_session(session)
        trial = session.create_group(name)
        return TrialStorage(trial)

    def get_trial(self, name, session=None):
        session = self._get_session(session)
        trial = session.get(name)
        return trial


class TrialStorage(dict):

    def __init__(self, group):
        self.group = group

    def __getitem__(self, key):
        return self.group.attrs[key]

    def __setitem__(self, key, val):
        self.group.attrs[key] = val

    def create_dataset(self, name, data, attrs=None):
        ds = self.group.create_dataset(name, data=data)
        for key, val in attrs.items():
            ds.attrs[key] = val


def participant_path(pid):
    return '{}'.format(pid)


def task_path(pid, experiment_id):
    return '{}/{}'.format(participant_path(pid), experiment_id)


def dt():
    dt = datetime.datetime.now()
    return str(dt.date()), str(dt.time())
