.. _development:

===========
Development
===========

Install
=======

Retrieve the source code::

    $ git clone git@github.com:axopy/axopy.git
    $ cd axopy

A virtual environment is a good way to set up a development environment::

    $ python -m venv .venv-dev
    $ source .venv-dev/bin/activate

Once in the virtual environment, you can install AxoPy in "development mode"
along with the development dependencies::

    (.venv-dev) $ pip intall -e .[dev]

If you take a look at the ``setup.py`` file, you'll see that this installs
everything from the ``requirements.txt`` file as well as the
``requirements-dev.txt`` file. This should be everything needed to run the
tests and build the documentation.

The Python Packaging Authority has much more detailed instructions here:
https://packaging.python.org/guides/installing-using-pip-and-virtualenv/


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

Once the build completes, you can open ``_build/html/index.html`` with your
browser to check the output.


Release
=======

This section is relevant only if you're an AxoPy maintainer. If you're just
interested in contributing to AxoPy, you can stop here.

PyPI
----

To cut a release, you'll need the `wheel <https://pypi.org/project/wheel/>`_
and `twine <https://pypi.org/project/twine/>`_ packages (these are not included
in the dev requirements which are for every-day development and CI).

Start by bumping the version number in the ``axopy.version`` module, then build
the source and wheel distributions::

    (.venv-dev) $ python setup.py sdist bdist_wheel

*Optional*: If you want to check first that all is well before pushing to PyPI,
you can upload the release packages to the test PyPI server first::

    (.venv-dev) $ twine upload --repository-url https://test.pypi.org/legacy dist/*

Now you can use twine to upload the release to PyPI. Note that you should
either remove everything from ``dist/`` first (if just using the command below)
or specify which files to upload::

    (.venv-dev) $ twine upload dist/*

Once everything looks good, you can tag the version bump commit and push the
tag up to GitHub.

conda-forge
-----------

After releasing on PyPI, you can update the release on conda-forge. Check
`their docs <https://conda-forge.org/docs/>`_ for insight into their process,
but the following is sufficient now that the infrastructure is in place.

Start by forking the `axopy-feedstock
<https://github.com/conda-forge/axopy-feedstock>`_ repo on GitHub. Edit the
``recipe/meta.yml`` file so its version string matches the PyPI version and
copy the SHA256 hash for the source dist (sdist) package (the ``tar.gz`` file)
from PyPI and paste it into the line below that. Commit the changes to your
fork then make a pull request against the conda-forge repository. If you're
a maintainer, you have push access to the repository so once CI passes, go
ahead and merge. The rest is automated.
