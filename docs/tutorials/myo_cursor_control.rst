.. _myo_cursor_control_tutorial:

=================================================
Myoelectric Cursor Control with Linear Regression
=================================================

This tutorial walks through the implementation of an experiment in which
subjects learn to control a circular cursor moving in 2D space using
electromyography (EMG) signals. This example covers most of the capabilities of
AxoPy.

The experiment has the following tasks:

- An "oscilloscope" displaying raw EMG signals. No data is saved for this task.
- A cursor following task in which subjects try to "follow" (using their wrist)
  a reference cursor as it moves around the screen. The trial data is simple,
  maybe a couple attributes such as the movement condition (the label for the
  cursor path). 
- A processing task that reads the EMG data, processes it through some
  preprocessing and feature extraction pipeline, and produces a dataset
  suitable for feeding into a scikit-learn regressor.
- The main cursor control task in which a linear regression is fit to the EMG
  features vs. cursor position data from the processing task and subjects learn
  to use wrist movements to control a cursor to hit targets on the screen.

Data Layout
-----------

::

    data/
        p0/
            cursor_following/
                trials.csv
                emg/
                    (raw EMG data for each trial)
                    1.hdf5
                    2.hdf5
                    ...
                cursor/
                    (cursor x, y position for each trial)
                    1.hdf5
                    2.hdf5
                    ...
            training_data/
                trials.csv [cursor_x, cursor_y, feature1, feature2, ...]
            cursor_practice/
                trials.csv [target_x, target_y, time_to_target]
                emg/
                    1.hdf5
                    2.hdf5
                    ...
                cursor/
                    1.hdf5
                    2.hdf5
                    ...
