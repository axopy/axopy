"""
Fit models
==========
Fits and saves the model for specified subject.

TODO

All models are saved to disk
for later use during real-time prosthesis control.
"""

import os

from argparse import ArgumentParser
from configparser import ConfigParser

import numpy as np
import pandas as pd
import h5py
import joblib


def calibrate(subject, n_dof):
    """Fits models.

    Parameters
    ----------
    subject : str
        Subject ID.
    n_dof : int
        Number of target degrees-of-freedom.

    Returns
    -------
    models : list
        List of (name, estimator/transformer) tuples.
    """
    root_trials = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', subject, 'calibration', 'trials.csv')
    root_glove_data = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'data', subject, 'calibration',
                                   'glove_proc.hdf5')

    trials = pd.read_csv(root_trials)
    glove_data = h5py.File(root_glove_data)

    min_ = np.zeros((N_DOF_HAND,))
    max_ = np.zeros((N_DOF_HAND,))

    for i, trial in trials.iterrows():
        data = glove_data.get(str(i)).value
        if trial.movement == 'thumb_flexion':
            max_[0] = np.max(data[0,:])
        elif trial.movement == 'thumb_extension':
            min_[0] = np.min(data[0,:])
        elif trial.movement == 'index_flexion':
            max_[1] = np.max(data[1,:])
        elif trial.movement == 'index_extension':
            min_[1] = np.min(data[1,:])
        elif trial.movement == 'middle_flexion':
            max_[2] = np.max(data[2,:])
        elif trial.movement == 'middle_extension':
            min_[2] = np.min(data[2,:])
        elif trial.movement == 'ring_flexion':
            max_[3] = np.max(data[3,:])
        elif trial.movement == 'ring_extension':
            min_[3] = np.min(data[3,:])
        elif trial.movement == 'little_flexion':
            max_[4] = np.max(data[4,:])
        elif trial.movement == 'little_extension':
            min_[4] = np.min(data[4,:])
        elif trial.movement == 'thumb_abduction':
            max_[5] = np.max(data[-1,:])
        elif trial.movement == 'thumb_adduction':
            min_[5] = np.min(data[-1,:])

    return [('cal_min', min_),
            ('cal_max', max_)]

def save_calibration_data(arrays, subject):
    """Saves all models/estimators to disk."""
    root_models = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', subject, 'models')
    if not os.path.exists(root_models):
        os.makedirs(root_models)

    for array in arrays:
        fname = os.path.join(root_models, array[0])
        joblib.dump(array[1], fname, compress=True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("subject", type=str,
                        help="Subject ID")
    args = parser.parse_args()

    cp = ConfigParser()
    cp.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'config.ini'))
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    N_DOF_HAND = cp.getint('hardware', 'n_dof_hand')

    arrays = calibrate(subject=args.subject, n_dof=N_DOF_HAND)
    save_calibration_data(arrays, subject=args.subject)
