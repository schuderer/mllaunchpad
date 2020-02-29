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

Unreleased
------------------------------------------------------------------------------

* |Deprecated| 'api:version:' to be removed from  configuration ('model:version:'
  will be the only location to specify both the model and the API version),
  `issue #66 <https://github.com/schuderer/mllaunchpad/issues/66>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Fix misleading error message at WSGI entry point if model could
  not be loaded,
  `issue #61 <https://github.com/schuderer/mllaunchpad/issues/61>`_,
  by `Bob Platte <https://github.com/bobplatte>`_.
* |Enhancement| Config file is now being checked for omitted required keys,
  `PR #65 <https://github.com/schuderer/mllaunchpad/pull/65>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Fixed| Use correct reference to werkzeug's FileStorage,
  `issue #63 <https://github.com/schuderer/mllaunchpad/issues/63>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.

0.0.7 (2020-01-28)
------------------------------------------------------------------------------

* |Fixed| Fix examples which could not be run on Windows,
  `issue #34 <https://github.com/schuderer/mllaunchpad/issues/34>`_,
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
* |Fixed| Correcting variable names in TEMPLATE_cfg.yml,
  `issue #43 <https://github.com/schuderer/mllaunchpad/issues/43>`_,
  by `Bart Driessen <https://github.com/Bart92>`_.
* |Feature| Added file upload support (multipart/form-data, experimental),
  `PR #47 <https://github.com/schuderer/mllaunchpad/pull/47>`_,
  by `Andreas Schuderer <https://github.com/schuderer>`_.
* |Feature| Added funcionality to include sub-config support,
  `issue #28 <https://github.com/schuderer/mllaunchpad/issues/28>`_,
  by `Elisa Partodikromo <https://github.com/planeetjupyter>`_.
* |Fixed| Changed config fallback file name to the more ugly ./LAUNCHPAD_CFG.yml,
  `direct commit <https://github.com/schuderer/mllaunchpad/commit/c012ee6a27f2da0cd9a7b57ab5aebf3257a71ffa>`_,
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
