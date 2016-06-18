Features
========

Features are statistics computed typically over short windows of the input
data. For example, you might take 100 samples of data from six channels of EMG
and calculate the root-mean-square value of each channel during that 100-sample
window of time. Features in hcibench are classes that take all of their
parameters in ``__init__`` and perform their operation on the input in
a ``compute`` method.


Time-Domain Features
--------------------

.. automodule:: hcibench.features.time
   :members:
