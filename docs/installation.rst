==============================================================================
Installation
==============================================================================


Stable release
------------------------------------------------------------------------------

To install ML Launchpad, run this command in your terminal:

.. code-block:: console

    $ pip install mllaunchpad

This is the preferred method for installing ML Launchpad, as it will
always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


Development version
------------------------------------------------------------------------------

The sources for ML Launchpad can be downloaded from the `Github repo`_.

If you just want to *use* the latest development version, the easiest way
is to use `pip`. The following fetches the code and installs the package:

.. code-block:: console

    $ pip install git+https://github.com/schuderer/mllaunchpad

If you want to actually be able to look at the code, you can either
clone the public repository:

.. code-block:: console

    $ git clone git://github.com/schuderer/mllaunchpad

Or download the `tarball`_:

.. code-block:: console

    $ curl -L https://github.com/schuderer/mllaunchpad/tarball/master > mllaunchpad.tar.gz

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/schuderer/mllaunchpad
.. _tarball: https://github.com/schuderer/mllaunchpad/tarball/master
