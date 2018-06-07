.. _development:

===========
Development
===========


Install
=======

Retrieve the source code::

    $ git clone git@github.com:ucdrascal/axopy.git
    $ cd axopy

A virtual environment is a good way to set up a development environment::

    $ python -m venv .venv-dev
    $ source .venv-dev/bin/activate

Once in the virtual environment, you can install AxoPy in "development mode"
along with the development dependencies::

    (.venv-dev) $ pip intall -e .[dev]

This will give you everything needed to run the tests and build the
documentation.

The Python Packaging Authority has much more detailed instructions here:
`https://packaging.python.org/guides/installing-using-pip-and-virtualenv/`


Test
====

pytest is used to find tests and run them::

    (.venv-dev) $ pytest


Document
========

To build the documentation locally, you can activate your dev environment,
``cd`` into the ``docs/`` directory, and run one of the build rules, like::

    (.venv-dev) $ cd docs/
    (.venv-dev) $ make html

If you aren't able to use ``make``, you could run the sphinx commands manually.
Look in the ``docs/Makefile`` to be sure, but it should be something like::

    (.venv-dev) $ sphinx-build -b html . _build/html


Release
=======

To cut a release, bump the version in the ``axopy.version`` module, then build
the source and wheel distributions::

    (.venv-dev) $ python setup.py sdist bdist_wheel

Now make sure you have twine installed (*it's not in the dev dependencies*),
and upload the release to PyPI::

    (.venv-dev) $ twine upload dist/*

If you want to check first that all is well before pushing to PyPI, you can
upload the release packages to the test PyPI server first::

    (.venv-dev) $ twine upload --repository-url https://test.pypi.org/legacy dist/*
