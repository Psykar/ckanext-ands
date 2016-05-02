.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org/Psykar/ckanext-ands.svg?branch=master
    :target: https://travis-ci.org/Psykar/ckanext-ands

.. image:: https://codecov.io/github/Psykar/ckanext-ands/badge.svg
  :target: https://codecov.io/github/Psykar/ckanext-ands


.. image:: https://img.shields.io/pypi/dm/ckanext-ands.svg
    :target: https://pypi.python.org/pypi/ckanext-ands/
    :alt: Downloads

.. image:: https://img.shields.io/pypi/v/ckanext-ands.svg
    :target: https://pypi.python.org/pypi/ckanext-ands/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/ckanext-ands.svg
    :target: https://pypi.python.org/pypi/ckanext-ands/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/status/ckanext-ands.svg
    :target: https://pypi.python.org/pypi/ckanext-ands/
    :alt: Development Status

.. image:: https://img.shields.io/pypi/l/ckanext-ands.svg
    :target: https://pypi.python.org/pypi/ckanext-ands/
    :alt: License

=============
ckanext-ands
=============

Allows submission of ANDS DOI requests for datasets.

Users can submit a DOI request which only sends an email to defined admins.
Sysadmins can directly add a DOI to a dataset from the Dataset's page via ANDS API.

------------
Requirements
------------

Tested with CKAN 2.5.1


------------
Installation
------------

To install ckanext-ands:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-ands Python package into your virtual environment::

     pip install ckanext-ands

3. Add ``ands`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config Settings
---------------

The following are required::

    ckanext.ands.DOI_API_KEY = xxyyzz
    ckanext.ands.shared_secret = asdfasdf

    # Email addresses to notify admins of a DOI request, comma separated
    ckanext.ands.support_emails = example@test.com,example2@test.com

    # THe publisher to use when submitting to ANDS
    ckanext.ands.publisher = 'A publisher'

    # The client ID proided by ANDS
    ckanext.ands.client_id = 123123

    # Set this to a URL you've enabled with ANDS, and requests from localhost will
    # use this url instead, useful for debugging
    ckanext.ands.debug_url = http://example.com

The following are optional (defaults are shown)::

    # DOI prefix to use for requests, defaults to ANDS default prefix
    ckanext.ands.doi_prefix = 10.5072/
    # Enable to add &debug=True to the tail of ANDS requests to get a bit more
    # info back on errors
    ckanext.ands.debug = False

------------------------
Development Installation
------------------------

To install ckanext-ands for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/Psykar/ckanext-ands.git
    cd ckanext-ands
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.ands --cover-inclusive --cover-erase --cover-tests


---------------------------------
Registering ckanext-ands on PyPI
---------------------------------

ckanext-ands should be availabe on PyPI as
https://pypi.python.org/pypi/ckanext-ands. If that link doesn't work, then
you can register the project on PyPI for the first time by following these
steps:

1. Create a source distribution of the project::

     python setup.py sdist

2. Register the project::

     python setup.py register

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the first release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags


----------------------------------------
Releasing a New Version of ckanext-ands
----------------------------------------

ckanext-ands is availabe on PyPI as https://pypi.python.org/pypi/ckanext-ands.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag -a 0.0.2
       git push --tags
