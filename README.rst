==============================================================================
About ML Launchpad
==============================================================================


.. image:: https://img.shields.io/pypi/v/mllaunchpad.svg?color=blue
        :target: https://pypi.python.org/pypi/mllaunchpad

.. image:: https://img.shields.io/pypi/pyversions/mllaunchpad.svg?color=blue
        :target: https://pypi.python.org/pypi/mllaunchpad

.. image:: https://img.shields.io/github/license/schuderer/mllaunchpad.svg?color=blue
     :target: https://pyup.io/repos/github/schuderer/mllaunchpad/
     :alt: LGPLv3 License

.. image:: https://img.shields.io/travis/schuderer/mllaunchpad.svg
       :target: https://travis-ci.org/schuderer/mllaunchpad

.. image:: https://coveralls.io/repos/github/schuderer/mllaunchpad/badge.svg?branch=master
     :target: https://coveralls.io/github/schuderer/mllaunchpad?branch=master

.. .. image:: https://pyup.io/repos/github/schuderer/mllaunchpad/shield.svg
..     :target: https://pyup.io/repos/github/schuderer/mllaunchpad/
..     :alt: Updates

.. image:: https://readthedocs.org/projects/mllaunchpad/badge/?version=latest
        :target: https://mllaunchpad.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
      :target: https://github.com/python/black
      :alt: Code Style Black


ML Launchpad lets you easily make Machine Learning models available as
REST API. It also offers lightweight model life cycle
management functionality.

What this means is that it creates a separation between machine learning
models and their environment. This way, you can run your model with
different data sources and on different environments, by just swapping
out the configuration, no code changes required. ML Launchpad makes your
model available as a business-facing *RESTful API*
without extra coding.

Currently, some basic model life cycle management is supported. Training
automatically persists a model in the model store together with its metrics,
and automatically retrieves it for launching its API or
re-training. Previous models are backed up.

-  TODO: better description of what problem ML Launchpad solves

The full documentation is available at https://mllaunchpad.readthedocs.io

Getting started
------------------------------------------------------------------------------

Direct installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

  $ pipenv install mllaunchpad

(Or ``pip install mllaunchpad`` if you don't have ``pipenv``)

Download the `example files <https://minhaskamal.github.io/DownGit/#/home?url=https://github.com/schuderer/mllaunchpad/tree/master/examples>`_
from the ML Launchpad GitHub repo. Some of them might require the installations
of some extra packages (e.g. scikit-learn), depending on what they demonstrate.

Source installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  TODO: prune this section/merge with `Contributing`.
   Please see `Installation` for a better source installation guide.

Download and unzip the repository as a zip file or clone the repository
using git:

.. code:: console

  $ git clone git@github.com:schuderer/mllaunchpad.git

Go to the ``mllaunchpad`` directory in a terminal:

.. code:: console

  $ cd mllaunchpad

If you have ``pipenv`` available (if not, it can be easily installed
using ``pip install pipenv``), create the environment with all the
dependencies.

.. code:: console

  $ pipenv install

(Use ``pipenv install --dev`` if you want to try out the examples – not
all development dependencies are needed for all examples, so don’t sweat
it if there are problems installing all of them)

This enviroment now contains all necessary packages. To activate this
enviroment, enter:

.. code:: console

  $ pipenv shell

Don’t have ``pipenv``? Have a look at the file ``Pipfile`` to see which
dependencies might need installing.

What's in the box?
------------------------------------------------------------------------------

If you installed from source, you see several subfolders, where ``mllaunchpad``
is the actual ML Launchpad package and the rest are examples and
development tools. You can safely ignore anything except the examples.

The ``examples`` contain a few example model implementations.
Look here for inspiration on how to use this package. Every model here
consists of at least three files:

* ``<examplename>_model.py``: the example’s actual model code

* ``<examplename>_cfg.yml``: the example’s configuration file

* ``<examplename>.raml``: example’s RESTful API specification.
  Used, among others, to parse and validate parameters.

* There are also some extra files, like CSV files to use, or datasource
  extensions.

The subfolder ``testserver`` contains an example for running a REST API
in gunicorn behind nginx.

Try Out the Examples
------------------------------------------------------------------------------

If you're using an environment manager, e.g. ``pipenv``, activate the
environment:

.. code-block:: console

  $ pipenv shell

In the following, it is assumed that the examples are located in the
current directory.

To train a very, *very* simple example model whose job it is to add two
numbers, use the command:

.. code:: console

  $ mllaunchpad -c addition_cfg.yml -t

(We give it a config file after the ``-c`` parameter, and ``-t`` is
short for the command ``--train``. There’s also a parameter ``-h`` to
print help)

Some log information is printed (you can give it a log-config file to
change this, see examples/logging_cfg.yml). At the end, it should say
“Created and stored trained model”, followed by something about metrics.

This created a model_store if it didn’t exist yet (which for now is just
a directory). For our examples, the model store is conveniently located
in the same directory. It contains our persisted ``addition`` model and
its metadata.

To re-test the previously trained model, use the command ``-r``:

.. code:: console

   $ mllaunchpad -c addition_cfg.yml -r

To run a (debugging-only!) REST API for the model, use the command
``-a``:

.. code:: console

   $ mllaunchpad -c addition_cfg.yml -a

To quickly try out out our fancy addition model API, open this link in a
browser: http://127.0.0.1:5000/add/v0/sum?x1=3&x2=2
(``curl http://127.0.0.1:5000/add/v0/sum?x1=3&x2=2`` on the command
line)

What next?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Have a look at the ``addition`` example’s python code (and comments),
its yml config, then look at the other examples. First, we suggest the
``iris`` example for intermediate complexity (although its prediction
code does quite some complex stuff to be compatible with three different
kinds of prediction usage, which is not really that realistic).

If you are wondering about the RAML file (which is a RESTful API
specification standard that is used in some corporate environments, and
a good idea in general), also look at the ``-g`` (generate raml) command
line parameter, which does a lot of work (almost all of it, in fact) for
getting you started with a first RAML.

Troubleshooting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case the console command ``mllaunchpad <your_arguments>`` is not recognized,
try:

.. code:: console

  $ python -m mllaunchpad <your_arguments>

If you get an error like ``No module named 'your_model'``, the file
``your_model.py`` is not in the python path. You can try to set the
`PYTHONPATH environment variable <https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_
to the path(s) to your file(s), or, if you're using ``mllaunchpad``
from your own python code, append the path(s) to
`sys.path <https://docs.python.org/3/library/sys.html?highlight=sys.path#sys.path>`_.

If you get ``ModuleNotFoundError: No module named 'mllaunchpad'`` (in
``mllaunchpad/__main__.py``), try to start flask the following way:

.. code:: console

   $ export FLASK_APP=mllaunchpad.wsgi:application
   $ export LAUNCHPAD_CFG=addition_cfg.yml
   $ flask run

(On Windows, use ``set`` instead of ``export``)

This problem appears to be connected to Flask restarting in different ways on
different installations. If you know what exactly this is about, `please let us
know`_.

Is it for me?
------------------------------------------------------------------------------

-  TODO: fill in this section

.. _please let us know: https://github.com/schuderer/mllaunchpad/issues/30.


Features
------------------------------------------------------------------------------

* TODO

Credits
-------

* Free software: GNU Lesser General Public License v3
* Documentation: https://mllaunchpad.readthedocs.io.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
