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

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import PredefinedSplit, GridSearchCV
from sklearn.metrics import r2_score
from sklearn.linear_model import Ridge

from sklearn_ext.wiener_filter import WienerFilter
from sklearn_ext.smoothing import SingleExponentialSmoothing


def fit_models(subject, n_dof):
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
    root_emg_data = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'data', subject, 'calibration',
                                 'emg_proc.hdf5')
    root_glove_data = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'data', subject, 'calibration',
                                   'glove_proc.hdf5')

    trials = pd.read_csv(root_trials)
    n_total_trials = trials.shape[0]
    emg_data = h5py.File(root_emg_data)
    n_features = emg_data.get('0').shape[0]
    glove_data = h5py.File(root_glove_data)

    # Collect training dataeee
    X = np.zeros((0, n_features))
    Y = np.zeros((0, n_dof))
    Y_r = np.zeros((0,), dtype=np.int)
    for trial in range(n_total_trials):
        emg_data_trial = emg_data.get(str(trial)).value.T
        X = np.append(X, emg_data_trial, axis=0)
        glove_data_trial = glove_data.get(str(trial)).value.T
        Y = np.append(Y, glove_data_trial, axis=0)
        rep = trials.iloc[trial].trial
        Y_r = np.append(Y_r, np.tile(rep, [glove_data_trial.shape[0]]), axis=0)

    n_df = Y.shape[1]

    mmsc = MinMaxScaler().fit(Y)
    Y_sc = mmsc.transform(Y)

    ps = PredefinedSplit(test_fold=Y_r)

    pipe_rr = Pipeline(steps=[
        ('ssc', StandardScaler()),
        ('rr', Ridge())])
    param_distr = {
        'rr__alpha': np.logspace(-3, 3, 20)
    }

    search = GridSearchCV(estimator=pipe_rr,
                          param_grid=param_distr,
                          cv=ps,
                          iid=False,
                          scoring='r2',
                          n_jobs=-1,
                          verbose=1)
    search.fit(X, Y_sc)

    # Get cross-validated predictions
    true = np.zeros((0, n_df))
    pred = np.zeros((0, n_df))
    for _, (train, test) in enumerate(ps.split(X, Y_sc)):
        estim = search.best_estimator_.fit(X[train, :], Y_sc[train, :])
        true = np.append(true, Y_sc[test, :], axis=0)
        pred_ = estim.predict(X[test, :])
        pred = np.append(pred, pred_, axis=0)

    # Tune alpha parameter of SingleExponentialSmoothing. This has to be done
    # explicitly (GridSearchCV won't work because we are fitting the
    # hyper-parameter of a Transformer). No need to use cross-validation here,
    # since no model parameters are estimated.
    alphas = np.linspace(0., 1., 50)
    scores = np.zeros((len(alphas),))
    for i, alpha in enumerate(alphas):
        sse = SingleExponentialSmoothing(alpha=alpha)
        scores[i] = r2_score(true, sse.transform(pred))
    best_alpha = alphas[np.argmax(scores)]
    print("Best R2 score: {:.2f}".format(np.max(scores)))

    return [('mdl', search),
            ('smoothing', SingleExponentialSmoothing(alpha=best_alpha)),
            ('target_scaler', mmsc)]


def save_models(models, subject):
    """Saves all models/estimators to disk."""
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
    cp.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'config.ini'))
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    N_DOF = cp.getint('hardware', 'n_dof')

    models = fit_models(subject=args.subject, n_dof=N_DOF)
    save_models(models, subject=args.subject)
