"""
Basic data storage framework backed by h5py.

group[root]
    group[participants]
        group[p<pid>]
            group[<experiment_id>]
                dataset[...]
                dataset[...]
    group[misc]
"""

import h5py
import datetime


class ExperimentDatabase(h5py.File):

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


class ExperimentBase(object):

    def __init__(self, group):
        self.group = group

    def create_session(self, name):
        return self.group.create_group(new_session_name(name))


def participant_path(pid):
    return '/participants/{}'.format(pid)


def experiment_path(pid, experiment_id):
    return '{}/{}'.format(participant_path(pid), experiment_id)


def new_session_name(name):
    dt = datetime.date.today().strftime('%Y-%m-%d')
    return '{}_{}'.format(dt, name)
