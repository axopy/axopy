import os
from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


install_requires = [
    'numpy',
    'scipy',
    'pandas',
    'h5py',
    #'pyqtgraph'
]
# add pyqt5 to requirements for pip installs only
# conda will complain because its package is just called "pyqt"
#if "CONDA_PREFIX" not in os.environ:
#    install_requires.append('pyqt5')


setup(
    name='axopy',
    version='0.1',
    description='Human-computer interface experimentation library',
    long_description=readme(),

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    keywords='human computer interface control electrophysiology',

    url='https://github.com/ucdrascal/axopy',
    author='Kenneth Lyons',
    author_email='ixjlyons@gmail.com',
    license='MIT',

    packages=find_packages(),

    install_requires=install_requires,
)
