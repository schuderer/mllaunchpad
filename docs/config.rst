.. highlight:: shell

==============================================================================
Configuration
==============================================================================

The configuration file is the glue that holds your ML-Launchpad-based application
together. It links the things on the "inside", that is, your model's
implementation, to the things on the "outside", such as the data connection
(:doc:`datasources`), as well as the API configuration.

**Sidenote**: You can use this to your advantage when developing and testing your machine learning
algorithm by using different configuration files for different purposes of your
development life cycle. That way, you can cleanly separate different environments
like development/testing/production, without having to touch your code (using the
same build) when between these environments.

For ML Launchpad to know how to do its job, it *always* needs a configuration.
To accommodate different ways of using ML Launchpad, you have different options of
providing the configuration. From most common to least common:

* Provide the path to the config file on the command line (``--config`` or ``-c`` option).
* Set the environment variable ``LAUNCHPAD_CFG`` to the path of the config file.
* Put a config file named ``LAUNCHPAD_CFG.yml`` in the current working directory.
* Call :meth:`~mllaunchpad.get_validated_config` with the path of the config file to get a config ``dict`` and provide it as an argument when calling :meth:`~mllaunchpad.predict`, :meth:`~mllaunchpad.retest` and/or :meth:`~mllaunchpad.train_model`.


=====================================   =======================================
Way of providing config                 When to use
=====================================   =======================================
``mllaunchpad --config <file>``         when developing; in some cases training
``LAUNCHPAD_CFG`` environment var       developing; when deployed (e.g. in production)
``./LAUNCHPAD_CFG.yml``                 deployed
in code                                 when using ``mllaunchpad`` functionality from another app instead of WSGI, e.g. as an Azure function
=====================================   =======================================

**Note**: Besides ``LAUNCHPAD_CFG``, there is also the ``LAUNCHPAD_LOG`` environment
variable, which, if provided, will be used as the `logging configuration file <https://docs.python.org/3.8/library/logging.config.html>`_.

.. _config_file:

Config File
------------------------------------------------------------------------------

The configuration file is written in `YAML <https://camel.readthedocs.io/en/latest/yamlref.html>`_ (.yml) format (used internally as
a Python ``dict``).

Here's an example configuration with comments:

.. code-block:: yaml

    plugins:  # Optionally specify any additional imports (only external DataSources/-Sinks for now, cf. ``DataSources``)
      - bogusdatasource
      - records_datasource

    datasources:  # This section is optional. Places to get data from, and how.
      petals:  # Name by which you want to refer to the datasource, e.g. using ``data_sources["petals"]``/
        # The properties ``type``, ``expires``, ``options`` and ``tags`` are present
        # in all types of datasources/datasinks.
        # All other properties are specific to the datasource type.
        type: csv  # Generic; the type of the datasource
        path: ./iris_train.csv  # Can also be a URL. Valid URL schemes: http, ftp, s3, and file.
        expires: 0  # -1: never (=cached forever), 0: immediately (=no caching), >0: time in seconds.
        options: {}  # Special kwargs to pass to the datasource's implementation
        tags: train  # String or list of strings. Valid are "train", "test" and/or "predict"
      petals_test:
        type: csv
        path: ./iris_holdout.csv
        expires: 3600
        options: {}
        tags: test
      # You can define as many datasources and datasinks as you like.
      # The tags "train", "test" and/or "predict" will determine which datasources/datasink
      # will be provided to which functions in your model implementation.
      # Any combination of tags with datasources/datasinks is valid.

    # datasinks:  # This section is optional. Places to put data. NOT needed for prediction outputs, unless you require batch output, special file formats, etc.
      # The configuration structure of datasinks is equivalent to that of datasources.

    model_store:  # Required. Where your model and metadata is persisted.
      location: ./model_store  # Directory on file system (local or remote).

    model:  # Required. Details about your model's implementation.
      name: TreeModel
      version: '0.0.1'  # Use semantic versioning (<breaking>.<adding>.<fix>), first segment will be used in API url as e.g. .../v1/...
      module: tree_model  # Main module of your functionality. Same as source code file name without .py
      # Put custom properties for your implementation here.
      # For example, to configure NLP-related aspects of your model (language, etc.),
      # to perform fewer iterations for testing purposes, etc.
      # It is not recommended to put low-level hyperparameters here.

    api:  # Optional. Details about your API. The API will start with /<api:name>/v<model:version[major]>/
      # If you don't specify the api property, you cannot use mllaunchpad's WSGI API.
      # You would eschew mllaunchpad's WSGI API if you want to make it available as
      # part of another service framework, e.g. AWS Lambda or Azure Functions.
      name: iris  # Name of the service API
      raml: tree.raml  # Path to the API's RAML definition (see next section)
      preload_datasources: False  # Load datasources into memory before any predictions. Only makes sense with caching (expires != 0).


Details on how to configure specific types of ``DataSources`` and ``DataSinks`` can be found
on the page :doc:`datasources`.

.. _plugins:

Plugins
------------------------------------------------------------------------------

In your :ref:`config_file`, you can optionally use a top-level ``plugins:`` key to
specify (a list of) modules that should be imported by ML Launchpad (currently only used
while initializing the :doc:`datasources`). If any of these plugins are in conflict
with other plugins or built-ins, the last-imported one has precedence over
the previous ones.

For example, if several :doc:`DataSource <datasources>` plugins offer to serve the
same type (e.g. ``csv``), the last one in the ``plugins:`` list will be chosen as the
designated ``csv`` handler, overruling both the built-in :class:`~mllaunchpad.resource.FileDataSource`
as well as any other ``csv``-serving DataSources listed before the one in question.

RAML API Definition
------------------------------------------------------------------------------

The API will be prefixed with ``/<api:name>/v<model:version[major]>/`` from your configuration
file (``/iris/v0/`` in above example). How the API actually looks beyond that is governed by your RAML file.

The `RAML specification language <https://github.com/raml-org/raml-spec/blob/master/versions/raml-08/raml-08.md>`_
has been chosen as the way to specify the API in a way that is compatible with common tools
(such as MuleSoft). Other languages do exist, and :doc:`contributions to support them are welcome <contributing>`.

The RAML is the contract between you and you service API's clients.
How to write a valid RAML is beyond the scope of this documentation.
But to help you starting out, there are various `examples <https://github.com/schuderer/mllaunchpad/tree/master/examples>`_,
and you can generate a basic :ref:`queryparams`-based RAML using :ref:`mllaunchpad --generate-raml <cli>`.

ML Launchpad understands a subset of RAML in order to automatically create APIs for
the (currently) three most common use cases (please note that they support GET as well as POST):

.. _queryparams:

Query Parameters
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

These are named parameters with a value.

E.g. in our "iris" example, in an API call that looks like
``/iris/v0/varieties?sepal.width=3&sepal.length=1.3[...]``
these would be ``sepal.width``, ``sepal.length`` etc., each
with one value:

.. code-block:: yaml

    /varieties:  # the resource name that comes after /iris/v0
      get:  # can also be post
        description: Get a prediction for the variety of iris flower based on measurements of physical petal and sepal dimensions
        queryParameters:
          sepal.length:
            displayName: Sepal Length
            type: number
            description: Measured length of iris flower sepals (flower leaves)
            example: 3.14
            required: false  # test, should be true
            minimum: 0
          sepal.width:
            displayName: Sepal Width
            type: number
            description: Measured width of iris flower sepals (flower leaves)
            example: 3.14
            required: false  # test, should be true
            minimum: 0
          # ...

The ``displayName``, ``type``, ``required``, ``example``, and ``minimum``/``maximum`` properties are
used by ML Launchpad for validation and logging. Others are ignored.

Your model's :meth:`~mllaunchpad.ModelInterface.predict` method will get passed an ``args_dict``
with a key for each query parameter, by which you can access the values.

Query parameters may be combined with :ref:`urlparams` (see `tree example <https://github.com/schuderer/mllaunchpad/tree/master/examples>`_).

**Sidenote**: While the technology that ML Launchpad uses under the hood also supports
requests with arbitrary JSON bodies which might work with ML Launchpad to provide more
complex values, this is at this point in time not officially supported.

.. _urlparams:

URL Parameters
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

A string in your APIs URL, e.g. ``/iris/v0/varieties/12``,
which usually identifies one record in the set of resources.

Example RAML:

.. code-block:: yaml

    /varieties:
      /{my_url_param_name}:  # parameter name to use
        get:  # post also possible
          queryParameters:  # Optional, just to demonstrate that this can be used in conjunction with query parameters.
            hallo:
              description: some demo query parameter in addition to the uri param
              type: string
              required: true
              enum: ['metric', 'imperial']
        # ...

The ``args_dict`` passed to your model's :meth:`~mllaunchpad.ModelInterface.predict` method
will contain the value under whatever name you gave it (here: "my_url_param_name"),
in addition to any other query parameters.

URL Parameters may be combined with :ref:`queryparams` (see `tree example <https://github.com/schuderer/mllaunchpad/tree/master/examples>`_).

Files
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Handling files (using ``multipart/form-data``) is also possible.

Example RAML:

.. code-block:: yaml

    /topics:
      post:
        description: Upload a PDF file to predict the topic for.
        body:
          multipart/form-data:
            formParameters:
              text:
                displayName: Optional alternative text of a client message
                type: string
                description: The plain text of a clients's letter, email, etc (uncleaned)
                required: false
            properties:
              file:
                description: The PDF file containing the client message, to be uploaded
                required: false
                type: file
                fileTypes: ["application/pdf"]
        # ...


The ``args_dict`` passed to your model's :meth:`~mllaunchpad.ModelInterface.predict` method
will contain a parameter named "file" with a FileStorage_
object. You can get its file name using ``args_dict["file"].filename`` and access its contents using ``args_dict["file"].stream``.
See the FileStorage_ documentation for more details.

As can be seen in the example, a file can be combined with :ref:`queryparams`. But it cannot
currently be combined with :ref:`urlparams` in ML Launchpad.

.. _FileStorage: https://werkzeug.palletsprojects.com/en/1.0.x/datastructures/#werkzeug.datastructures.FileStorage
