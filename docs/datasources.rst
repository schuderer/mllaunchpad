.. highlight:: yaml

==============================================================================
DataSources and DataSinks
==============================================================================

:class:`DataSources <mllaunchpad.resource.DataSource>` and
:class:`DataSinks <mllaunchpad.resource.DataSink>` are what loosely couples
your model's code to the data.

From your model's code, instead of accessing
your data locations directly, you access your data via the
:class:`DataSources <mllaunchpad.resource.DataSource>` and
:class:`DataSinks <mllaunchpad.resource.DataSink>` that are provided by ML Launchpad.
To your code, all :class:`DataSources <mllaunchpad.resource.DataSource>` and
:class:`DataSinks <mllaunchpad.resource.DataSink>` behave the same and are used
the same way for the same data format (``DataFrames``, raw files, etc.).

For example, to obtain a pandas ``DataFrame``,
use the :class:`~mllaunchpad.resource.DataSource`'s
:meth:`~mllaunchpad.resource.DataSource.get_dataframe` method.
Your code does not need to know
whether your data was originally obtained from a database, file, or web service.

As :class:`DataSources <mllaunchpad.resource.DataSource>` and
:class:`DataSinks <mllaunchpad.resource.DataSink>` are very similar, we will
use the term :class:`~mllaunchpad.resource.DataSource` below meaning either.

Different subclasses of :class:`DataSources <mllaunchpad.resource.DataSource>`
provide you with different kinds of connections. In the following sections, you can find
lists of built-in and external :class:`DataSources <mllaunchpad.resource.DataSource>`
and :class:`DataSinks <mllaunchpad.resource.DataSink>`.

Each subclass of :class:`DataSources <mllaunchpad.resource.DataSource>` (e.g. :class:`~mllaunchpad.resource.FileDataSource`,
:class:`~mllaunchpad.resource.OracleDataSource`)
serves one or several ``types`` (e.g. ``csv``, ``euro_csv``, ``dbms.oracle``).
You specify the ``type`` in your DataSource's :doc:`configuration <config>`.
The same ``type`` can even be served by several different
:class:`~mllaunchpad.resource.DataSource` subclasses, in which case the
:doc:`last-imported plugin <config>`.

Here is an example for a configured
:class:`~mllaunchpad.resource.FileDataSource`::

    datasources:
      my_datasource:
        type: csv
        path: ./iris_train.csv
        expires: 0
        options: {}
        tags: train

Where the parts of this examples are:

* ``datasources`` (or ``datasinks``; optional): Can contain
  as many child elements (configured DataSources or DataSinks) as you like.
* ``my_datasource``: The name by which you want to refer to a specific configured DataSource.
  Used to get data, e.g.: ``data_sources["my_datasource"].get_dataframe()``. This name is up to you to choose.
* ``type`` (required in every DataSource): the ``type`` that a DataSource needs to
  serve in order to be chosen for you. In this case, when ML Launchpad looks up
  which DataSources serve the ``csv`` type, it finds
  :class:`~mllaunchpad.resource.FileDataSource` and will use it.
* ``path`` (specific to :class:`~mllaunchpad.resource.FileDataSource`):
  The path of the file. Every DataSource has its own specific properties
  which are part of the DataSource's documentation (see the next section for built-ins).
* ``expires`` (required in every DataSource): This controls caching of the data.
  0 means that it expires immediately, -1 that it never expires, and another
  number specifies the number of seconds after the cached data expires and
  should be gotten afresh from the source.
* ``tags`` (required in every DataSource): a combination of one or several of
  the possible tags ``train``, ``test`` and ``predict`` (use [brackets] around
  more than one tag). This determines the model function(s) the DataSource will be
  made available for.

For more complete examples, have a look at the :ref:`tutorial` or at the
`examples <https://github.com/schuderer/mllaunchpad/blob/master/examples/>`_ (:download:`download <_static/examples.zip>`).

Please note that :class:`DataSources <mllaunchpad.resource.DataSource>`
and :class:`DataSinks <mllaunchpad.resource.DataSink>` will be initialized
for you by ML Launchpad depending on your configuration.
Your code will just get "some" DataSource, but won't have to import, initialize, or
even know the name of the DataSource class that is used under the hood.

When needing to use e.g. several tables that reside in the same data base, it
is useful to not have to configure their connection details for every one
of the DataSources that correspond with those tables, but configure a
connection only once. For this, you specify a separate ``dbms:`` section in your
configuration where you give each connection a name (e.g. ``my_connection``) which
you can refer to in your ``datasource`` config by a type like e.g. ``dmbs.my_connection``.
See :class:`~mllaunchpad.resource.OracleDataSource` below for an example.

Built-in DataSources and DataSinks
------------------------------------------------------------------------------
When you ``pip install mllaunchpad``, it comes with a number of built-in
DataSources and DataSinks that are ready to use without needing to specify
any ``plugins: []`` in the :doc:`config`.

Their documentation follows hereunder.

.. autoclass:: mllaunchpad.resource.FileDataSource
   :noindex:
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: mllaunchpad.resource.FileDataSink
   :noindex:
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: mllaunchpad.resource.OracleDataSource
   :noindex:
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: mllaunchpad.resource.OracleDataSink
   :noindex:
   :members:
   :inherited-members:
   :undoc-members:


External DataSources and DataSinks
------------------------------------------------------------------------------
The datasources here are not part of core ML Launchpad.

To be able to use them:

1. install them if they support it, or copy them into your project's source code directory;
2. add their import statement to the ``plugins:`` section of your configuration, e.g.

.. code-block:: yaml

    plugins:  # Add this line if it's not already in your config
      - some_module.my_datasource  # for a file in the 'some_module' directory called 'my_datasource.py'

Their documentation follows hereunder.

.. autoclass:: examples.impala_datasource.ImpalaDataSource
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: examples.records_datasource.RecordsDbDataSource
   :members:
   :inherited-members:
   :undoc-members:
