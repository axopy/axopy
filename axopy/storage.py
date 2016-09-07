"""
Basic data storage framework backed by h5py.
"""

import h5py
import datetime


class ExperimentDatabase(h5py.File):

    def __init__(self, *args, **kwargs):
        super(ExperimentDatabase, self).__init__(*args, **kwargs)
        self.create_group(participants_path())

    def create_participant(self, pid):
        return self.create_group(participant_path(pid))

    def get_participant(self, pid):
        return self.get(participant_path(pid))

    def require_participant(self, pid):
        return self.require_group(participant_path(pid))

    def create_experiment(self, pid, name):
        return self.create_group(experiment_path(pid, name))

    def get_experiment(self, pid, name):
        return self.get(experiment_path(pid, name))

    def require_experiment(self, pid, name):
        return self.require_group(experiment_path(pid, name))

    def get_participants(self):
        return list(self[participants_path()].keys())


def participants_path():
    return '/participants'


def participant_path(pid):
    return '{}/{}'.format(participants_path(), pid)


def experiment_path(pid, experiment_id):
    return '{}/{}'.format(participant_path(pid), experiment_id)


def new_session_name(name):
    dt = datetime.date.today().strftime('%Y-%m-%d')
    return '{}_{}'.format(dt, name)
