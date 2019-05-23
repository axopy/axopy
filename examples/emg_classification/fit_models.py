
import os

from argparse import ArgumentParser
from configparser import ConfigParser

import numpy as np
import pandas as pd
import h5py
import joblib

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis


def fit_models(subject, trim_samples):
    """Fits models.

    Parameters
    ----------
    subject : str
        Subject ID.
    trim_sampels : int
        Number of samples to discard at start and end of each trial.

    Returns
    -------
    models : list
        List of (name, estimator/transformer) tuples.
    """
    root_trials = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', subject, 'calibration', 'trials.csv')
    root_data = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'data', subject, 'calibration', 'data_proc.hdf5')

    trials = pd.read_csv(root_trials)
    n_total_trials = trials.shape[0]
    data = h5py.File(root_data)
    n_features = data.get('0').shape[0]

    # Collect training data
    X = np.zeros((0, n_features))
    Y = np.zeros((0,), dtype=np.str_)
    for trial in range(n_total_trials):
        data_trial = data.get(str(trial)).value.T
        data_trial_tr = data_trial[trim_samples:, :]
        X = np.append(X, data_trial_tr, axis=0)
        label = trials.iloc[trial].movement
        Y = np.append(Y, np.tile(label, [data_trial_tr.shape[0]]), axis=0)

    ssc = StandardScaler().fit(X)
    X_tf = ssc.transform(X)

    le = LabelEncoder().fit(Y)
    Y_le = le.transform(Y)

    clf = LinearDiscriminantAnalysis().fit(X_tf, Y_le)

    return [('input_scaler', ssc),
            ('output_encoder', le),
            ('classifier', clf)]


def save_models(models, subject):
    root_models = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', subject, 'models')
    if not os.path.exists(root_models):
        os.makedirs(root_models)

    for model in models:
        fname = os.path.join(root_models, model[0])
        joblib.dump(model[1], fname, compress=True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("subject", type=str,
                        help="Subject ID")
    args = parser.parse_args()

    cp = ConfigParser()
    cp.read('config.ini')
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    trim_length = 1.0 # TODO: ini file
    trim_samples = int(trim_length / READ_LENGTH)

    models = fit_models(subject=args.subject, trim_samples=trim_samples)
    save_models(models, subject=args.subject)
