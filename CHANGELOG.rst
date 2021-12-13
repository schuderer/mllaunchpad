==============================================================================
Changelog
==============================================================================

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

.. role:: raw-html(raw)
   :format: html

.. Use one of these tags for marking your contribution and add
   your contribution to the "Unreleased" section.
   Contributions should be ordered first by their tag (in the order
   in which they are listed here), and related contributions (e.g.
   affecting the same module/component) should be next to each other.
.. |Security| replace:: :raw-html:`<span style="font-family: Sans-Serif; font-size: 0.6em; color: white; font-weight: bold; padding: 0.05em; border-radius: 0.2em; display: inline-block; background-color: #666699">&nbsp;SECURITY&nbsp;</span>`
.. |Fixed| replace:: :raw-html:`<span style="font-family: Sans-Serif; font-size: 0.6em; color: white; font-weight: bold; padding: 0.05em; border-radius: 0.2em; display: inline-block; background-color: #993300">&nbsp;FIXED&nbsp;</span>`
.. |Enhancement| replace:: :raw-html:`<span style="font-family: Sans-Serif; font-size: 0.6em; color: white; font-weight: bold; padding: 0.05em; border-radius: 0.2em; display: inline-block; background-color: #003399">&nbsp;ENHANCEMENT&nbsp;</span>`
.. |Feature| replace:: :raw-html:`<span style="font-family: Sans-Serif; font-size: 0.6em; color: white; font-weight: bold; padding: 0.05em; border-radius: 0.2em; display: inline-block; background-color: #339933">&nbsp;FEATURE&nbsp;</span>`
.. |Deprecated| replace:: :raw-html:`<span style="font-family: Sans-Serif; font-size: 0.6em; color: white; font-weight: bold; padding: 0.05em; border-radius: 0.2em; display: inline-block; background-color: orange">&nbsp;DEPRECATED&nbsp;</span>`
.. |Removed| replace:: :raw-html:`<span style="font-family: Sans-Serif; font-size: 0.6em; color: white; font-weight: bold; padding: 0.05em; border-radius: 0.2em; display: inline-block; background-color: black">&nbsp;REMOVED&nbsp;</span>`

.. Placeholder for empty Unreleased section:
   * No contributions yet. :doc:`Be the first to add one! <contributing>` :)

Unreleased
------------------------------------------------------------------------------

   * No contributions yet. :doc:`Be the first to add one! <contributing>` :)

1.0.0 (2021-12-13)
------------------------------------------------------------------------------

* |Feature| Add training metadata reporting and querying,
  `issue #142 <https://github.com/schuderer/mllaunchpad/issues/142>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Feature| Add support for typed CSVs (option ``dtypes_path`` of
  :class:`FileDataSource <mllaunchpad.datasources.FileDataSource>` and
  :class:`FileDataSink <mllaunchpad.datasources.FileDataSink>`),
  `issue #127 <https://github.com/schuderer/mllaunchpad/issues/127>`_,
  by `Elisa Partodikromo <https://github.com/planeetjupyter>`_.
* |Feature| Add Spark support (experimental), see ``examples/spark_datasource.py``
  and `issue #145 <https://github.com/schuderer/mllaunchpad/issues/145>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| FileDataSink (`csv`, `euro_csv`, `raw` DataSink types) now attempts to create missing paths if required,
  `issue #148 <https://github.com/schuderer/mllaunchpad/issues/148>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Keep generated RAML files free of command line messages,
  `issue #126 <https://github.com/schuderer/mllaunchpad/issues/126>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Change default text file encoding to UTF-8 for config files, text_file Data Sources/Sinks and JSON model metadata.
  **NOTE:** If you have been using non-ASCII characters in any of the above, you will need to check that the encoding of the relevant existing file(s) is UTF-8.
  `issue #128 <https://github.com/schuderer/mllaunchpad/issues/128>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Explicitly support repeated query parameters (and array types like number[]) through RAML definition.
  Remove IP from training metadata due to problem on macOS Big Sur.
  Fix doc build by pinning `Sphinx dependency docutils <https://github.com/sphinx-doc/sphinx/issues/9841>`_ to version 0.17.1.
  `issue #147 <https://github.com/schuderer/mllaunchpad/issues/147>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.

1.0.0 (2020-06-08)
------------------------------------------------------------------------------

* |Fixed| ``mllaunchpad --verbose`` now correctly logs DEBUG information,
  `issue #119 <https://github.com/schuderer/mllaunchpad/issues/119>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Fixed an issue where builtin DataSources could not be found when configured,
  `issue #118 <https://github.com/schuderer/mllaunchpad/issues/118>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Readthedocs now shows the up-to-date :doc:`API docs <mllaunchpad>`,
  `issue #110 <https://github.com/schuderer/mllaunchpad/issues/110>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| Added ``chunksize`` parameter for piecemeal data reading to builtin DataSources,
  `issue #120 <https://github.com/schuderer/mllaunchpad/issues/120>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Feature| Added functionality to better support unit testing in model development
  (added optional parameters to :meth:`mllaunchpad.train_model`, :meth:`mllaunchpad.retest`
  and :meth:`mllaunchpad.predict`, added :meth:`mllaunchpad.get_validated_config_str`),
  `issue #116 <https://github.com/schuderer/mllaunchpad/issues/116>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Feature| Added generic SqlDataSource for RedShift, Postgres, MySQL, SQLite, Oracle,
  Microsoft SQL (ODBC), and their dialects,
  `issue #121 <https://github.com/schuderer/mllaunchpad/issues/121>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| New command line interface (usage changes only slightly, see issue),
  `issue #77 <https://github.com/schuderer/mllaunchpad/issues/77>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| DataSource caching overhaul: data cached separately for different
  :meth:`params <mllaunchpad.datasources.FileDataSource.get_dataframe>`,
  configurable ``cache_size``,
  `issue #97 <https://github.com/schuderer/mllaunchpad/issues/97>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Removed| Removed 'api:version:' (deprecated since 0.1.0) from  configuration
  ('model:version:' is now the only location to specify both the model and the API version),
  `issue #66 <https://github.com/schuderer/mllaunchpad/issues/66>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.

0.1.2 (2020-04-23)
------------------------------------------------------------------------------

* |Fixed| Oracle DataSource's ``get_dataframe`` now interprets ``Null`` as ``nan``,
  `issue #86 <https://github.com/schuderer/mllaunchpad/issues/86>`_,
  by `Bob Platte <https://github.com/bobplatte>`_.
* |Enhancement| Add a truckload of unit tests,
  `issue #46 <https://github.com/schuderer/mllaunchpad/issues/46>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.

0.1.1 (2020-04-02)
------------------------------------------------------------------------------

* |Fixed| Fix missing classifiers on PyPI,
  by `Andreas Schuderer <https://github.com/schuderer>`_.

0.1.0 (2020-04-02)
------------------------------------------------------------------------------

* |Fixed| Fix misleading error message at WSGI entry point if model could
  not be loaded,
  `issue #61 <https://github.com/schuderer/mllaunchpad/issues/61>`_,
  by `Bob Platte <https://github.com/bobplatte>`_.
* |Fixed| Use correct reference to werkzeug's FileStorage,
  `issue #63 <https://github.com/schuderer/mllaunchpad/issues/63>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| Document DataSources and DataSinks,
  `issue #88 <https://github.com/schuderer/mllaunchpad/issues/88>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| Document configuration,
  `issue #67 <https://github.com/schuderer/mllaunchpad/issues/67>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| Add utility user function ``order_columns`` for enforcing equal
  data column order between data sources and API parameters,
  `issue #37 <https://github.com/schuderer/mllaunchpad/issues/37>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| Config file is now being checked for omitted required keys,
  `PR #65 <https://github.com/schuderer/mllaunchpad/pull/65>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Feature| Add Impala DataSource (in examples),
  `issue #4 <https://github.com/schuderer/mllaunchpad/issues/4>`_,
  by `Elisa Partodikromo <https://github.com/planeetjupyter>`_.
* |Deprecated| 'api:version:' to be removed from  configuration ('model:version:'
  will be the only location to specify both the model and the API version),
  `issue #66 <https://github.com/schuderer/mllaunchpad/issues/66>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.

0.0.7 (2020-01-28)
------------------------------------------------------------------------------

* |Fixed| Fix examples which could not be run on Windows,
  `issue #34 <https://github.com/schuderer/mllaunchpad/issues/34>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Correcting variable names in TEMPLATE_cfg.yml,
  `issue #43 <https://github.com/schuderer/mllaunchpad/issues/43>`_,
  by `Bart Driessen <https://github.com/Bart92>`_.
* |Fixed| Changed config fallback file name to the more ugly ./LAUNCHPAD_CFG.yml,
  `direct commit <https://github.com/schuderer/mllaunchpad/commit/c012ee6a27f2da0cd9a7b57ab5aebf3257a71ffa>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Migrate from ``pipenv`` to ``pip`` with ``requirements/*.txt``,
  `issue #36 <https://github.com/schuderer/mllaunchpad/issues/36>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| Extend documentation: getting started, use case, structure,
  deployment requirements, usage,
  `issue #18 <https://github.com/schuderer/mllaunchpad/issues/18>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Enhancement| Improve contribution documentation,
  `issue #35 <https://github.com/schuderer/mllaunchpad/issues/35>`_,
  by `Gosia Rorat <https://github.com/gosiarorat>`_.
* |Feature| Added funcionality to include sub-config support,
  `issue #28 <https://github.com/schuderer/mllaunchpad/issues/28>`_,
  by `Elisa Partodikromo <https://github.com/planeetjupyter>`_.
* |Feature| Added file upload support (multipart/form-data, experimental),
  `PR #47 <https://github.com/schuderer/mllaunchpad/pull/47>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.


0.0.5 (2019-07-20)
------------------------------------------------------------------------------

* |Fixed| Link from GitHub README to documentation,
  `issue #18 <https://github.com/schuderer/mllaunchpad/issues/18>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.

0.0.1 (2019-07-18)
------------------------------------------------------------------------------

* |Feature| First release on PyPI,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
