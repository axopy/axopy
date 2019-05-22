
import os

from argparse import ArgumentParser
from configparser import ConfigParser

import numpy as np
import pandas as pd
import h5py
import joblib

from scipy.stats import uniform

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.model_selection import PredefinedSplit, RandomizedSearchCV
from sklearn.metrics import accuracy_score

from sklearn_ext.discriminant_analysis import RegularizedDiscriminantAnalysis
from sklearn_ext.roc_analysis import RocThreshold

def fit_models(subject, trim_samples, n_iter, fpr_threshold):
    """Fits models.

    Parameters
    ----------
    subject : str
        Subject ID.
    trim_sampels : int
        Number of samples to discard at start and end of each trial.
    n_iter : int
        Number of iterations for RandomizedSearchCV
    fpr_threshold : float
        FPR threshold for estimating ROC thresholds.

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
    Y_r = np.zeros((0,), dtype=np.int)
    for trial in range(n_total_trials):
        data_trial = data.get(str(trial)).value.T
        data_trial_tr = data_trial[trim_samples:, :]
        X = np.append(X, data_trial_tr, axis=0)
        label = trials.iloc[trial].movement
        rep = trials.iloc[trial].trial
        Y = np.append(Y, np.tile(label, [data_trial_tr.shape[0]]), axis=0)
        Y_r = np.append(Y_r, np.tile(rep, [data_trial_tr.shape[0]]), axis=0)

    ps = PredefinedSplit(test_fold=Y_r)

    le = LabelEncoder().fit(Y)
    Y_le = le.transform(Y)

    pipe_lda = Pipeline(steps=[
        ('ssc', StandardScaler()),
        ('clf', LinearDiscriminantAnalysis())])

    pipe_rda = Pipeline(steps=[
        ('ssc', StandardScaler()),
        ('clf', RegularizedDiscriminantAnalysis())])
    param_distr = {
        'clf__reg_param_alpha': uniform,
        'clf__reg_param_gamma': uniform
    }
    search = RandomizedSearchCV(estimator=pipe_rda,
                                param_distributions=param_distr,
                                cv=ps,
                                iid=False,
                                scoring=['accuracy', 'neg_log_loss'],
                                refit='neg_log_loss',
                                n_iter=n_iter,
                                n_jobs=-1,
                                verbose=1)
    search.fit(X, Y_le)

    print("Mean best RDA accuracy: {:.4f}".format(
        search.cv_results_['mean_test_accuracy'][search.best_index_]))
    print("Mean LDA accuracy: {:.4f}".format(
        cross_val_score(pipe_lda, X, Y_le, cv=ps).mean()))

    print("Mean best RDA negative logloss: {:.4f}".format(
        search.cv_results_['mean_test_neg_log_loss'][search.best_index_]))
    print("Mean LDA negative logloss: {:.4f}".format(
        cross_val_score(pipe_lda, X, Y_le, cv=ps,
        scoring='neg_log_loss').mean()))

    # ROC thresholds (using 50% train test split)
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y_le, test_size=0.5)
    clf = search.best_estimator_.steps[1][1]
    clf.fit(X_train, Y_train)

    rt = RocThreshold(strategy='max_random', fpr_threshold=fpr_threshold)
    rt.fit(le.inverse_transform(Y_test), clf.predict_proba(X_test))

    return [('input_scaler', search.best_estimator_.steps[0][1]),
            ('output_encoder', le),
            ('classifier', search.best_estimator_.steps[1][1]),
            ('roc_thresholds', rt)]


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
    cp.read('config.ini')
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    TRIM_LENGTH = cp.getfloat('fit', 'trim_length')
    trim_samples = int(TRIM_LENGTH / READ_LENGTH)
    N_ITER = cp.getint('fit', 'n_iter')
    FPR_THRESHOLD = cp.getfloat('fit', 'fpr_threshold')

    models = fit_models(subject=args.subject,
                        trim_samples=trim_samples,
                        n_iter=N_ITER,
                        fpr_threshold=FPR_THRESHOLD)
    save_models(models, subject=args.subject)
