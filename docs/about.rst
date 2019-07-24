==============================================================================
Why ML Launchpad
==============================================================================


What is it?
------------------------------------------------------------------------------


ML Launchpad is an extensible Python package which makes
it easy to publish Machine Learning models as
RESTful APIs.

It separates the Machine Learning side
(how to train, test and to predict) from the
environment-specific aspects (local or cloud deployment of the API,
database connections, format validation, model storage, etc.)

Configure and deploy ML Launchpad *once*, and the model developer
can publish an unlimited number of different Machine Learning
algorithms as they
are needed, relieving them of having to deal with
deployment specifics.

While most approaches for streamlining Machine Learning solutions
force you to select a particular set of machine learning libraries
and/or a particular platform, ML Launchpad is agnostic to those,
retaining the flexibility to choose any algorithm and any
platform.

Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On the environment side, ML Launchpad sports a configurable
REST API (using Flask), that can be run on any WSGI-compatible
server.

Retrieving and persisting data is done through an extensible
abstraction mechanism, called Data Sources and Data Sinks.
Common types of Data Sources and Sinks like relational
databases and CSV files are already included.

.. image:: _static/schematic.png
        :alt: ML Launchpad Schematic

The model "payload" itself is the only time where code needs
to be produced by the model developer. Here, the developer is
basically filling in three functions in an R or Python template
(Spark support is planned):

* ``train`` - uses data provided by Data Sources and returns
  a trained model object
* ``test`` - uses the provided model object and Data Sources and
  returns metrics about the model
* ``predict`` - uses the provided model object and (validated)
  API parameters to carry out a prediction and returns the
  prediction result

This is all the programming that is needed.

While enforcing the division into three functions might seem
restrictive at first glance, in reality
it makes simple things straightforward, while complex things are
still achievable without complication due to the flexibility
and configurability of ML Launchpad.

ML Launchpad handles how these functions are called, and what
to do with the results. That way, the model can, unchanged,
run on e.g. a Windows developer laptop using
flat files, or a Linux cloud instance using databases.

How the model and the environment work together is defined using
a configuration file. The RESTful API is defined using a
RAML file (RESTful API Modeling Language).

Life of a Model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, the model developer pip-installs the ``mllaunchpad``
package so they can use it in their project.

Then, they use the ``TEMPLATE_*`` files
available in the ``examples`` directory to create three
files in their project: a model file
like ``<my_model_name>.py``, a configuration file like
``<my_model>_cfg.yml`` and a REST API definition file like
``<my_model>.raml``.

(To help with getting the RAML file started, the command
``mllaunchpad -g my_source`` is used.)

If everything is filled in, it is time to train the model:

.. code:: console

  $ mllaunchpad -c <my_model>_cfg.yml -t

The trained model is persisted in the ``model_store`` location
defined in the configuration file.

Note: Feel free to use the command line or the ML Launchpad's
Python convenience API functions. Instead of using the ``-c``
parameter, the location of the configuration
file can also provided by setting the ``LAUNCHPAD_CFG`` environment
variable.

To test, the developer runs a (debugging-only!) REST API for
the model, using the command
``-a``:

.. code:: console

   $ mllaunchpad -c <my_model>_cfg.yml -a

They test the API, and if it works as expected, the model
can be used in a proper WSGI server, like for example
gunicorn behind nginx.

There comes a time when the deployed model starts to get out of date.
To re-test the previously trained model, use the command ``-r``
or the Python API convenience functions.

.. code:: console

   $ mllaunchpad -c <my_model>_cfg.yml -r


Extensibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ML Launchpad is designed with extensibility in mind.

The ML Launchpad package does not come with the whole kitchen sink,
but still contains enough functionality to be able to deploy a
complete Machine Learning API.

If the functionality which is provided is not sufficient,
it can be extended in two major ways:

Without needing to modify the base package:

* Adding new Data Source and Data Sink Extensions
* Adding new Model Type Extensions
* Using the Python Convenience API for implementing custom
  model life cycle management logic

Through contributions to the base package:

* Adding support for OpenAPI specs in addition to RAML
* Anything else :)

New types of Data Sources and Data Sinks can be added simply
by extending the base classes in a Python module of your own and
listing it in the ``plugins:`` section of your configuration.

New types of models (programming languages etc.) can be supported
by creating a python model which acts as a bridge to the desired
technology. In that sense, models already act like extensions.

Support for ``pip install``-able extensions is on the roadmap,
too. If you want to help, that's awesome! Let your voice be
heard at the corresponding GitHub issue.
