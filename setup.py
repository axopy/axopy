import os
import codecs
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_requirements(fpath):
    content = read(fpath)
    reqs = []
    for req in content.split('\n'):
        if req == '' or req.startswith('#'):
            continue

        # conda-forge PyQt5 package is just called pyqt (instead of pyqt5), so
        # don't add it to install_requires or it will be installed again with
        # pip (which fails for Python < 3.5)
        if req.startswith('pyqt5') and 'CONDA_PREFIX' in os.environ:
            continue

        reqs.append(req)

    return reqs


exec(read('axopy', 'version.py'))

setup(
    name='axopy',
    version=__version__,
    description='Human-computer interface experimentation library',
    long_description=read('README.rst'),

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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='human computer interface control electrophysiology',

    url='https://github.com/ucdrascal/axopy',
    author='Kenneth Lyons',
    author_email='ixjlyons@gmail.com',
    license='MIT',

    packages=find_packages(),

    install_requires=find_requirements('requirements.txt'),
    extras_require={
        'dev': find_requirements('requirements-dev.txt'),
    },
)
