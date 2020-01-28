.. highlight:: shell

==============================================================================
Contributing
==============================================================================

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
------------------------------------------------------------------------------

Report Bugs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Report bugs at https://github.com/schuderer/mllaunchpad/issues.

If you are reporting a bug, please search the existing issues to
make sure that it is not a duplicate, and include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ML Launchpad could always use more documentation, whether as part of the
official ML Launchpad docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/schuderer/mllaunchpad/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------------------------------------------------------------------------

Ready to contribute? Here's how to set up ``mllaunchpad`` for local development.

1. Fork the ``mllaunchpad`` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/mllaunchpad.git

3. Install your local copy for development. We recommend to use a
   virtual environment and are going to use ``venv`` in our examples
   (though any kind of virtual environment should work)::

    $ cd mllaunchpad/
    $ python -m venv .venv

   Activate the virtual environment::

   $ source .venv/bin/activate

   (On Windows, use the command ``.venv\Scripts\activate.bat``.)

   Install the development requirements (this also installs
   the package in editable mode)::

   $ pip install -r requirements/dev.txt

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally. Don't forget to create tests for
   your code.
   Recommended style is Google style, particularly `docstrings <https://google.github.io/styleguide/pyguide.html#381-docstrings>`_.

   Add the upstream remote. This saves a reference to the main mllaunchpad
   repository, which you can use to keep your repository synchronized
   with the latest changes::

    $ git remote add upstream https://github.com/schuderer/mllaunchpad.git

   It is often helpful to keep your local branch synchronized with the latest
   changes of the main mllaunchpad repository::

    $ git fetch upstream
    $ git merge upstream/master

5. To quickly test just the relevant modified files while still developing::

    $ pytest tests.test_module_testing_your_changes

   When you're done making changes, run ``nox`` to check that your changes
   pass all style checks and tests. This also reformats your code::

    $ nox

   For more fine-grained control, you can ``nox -s a_session_name`` to
   only perform specific tests or checks. Run ``nox -l`` for a list of sessions.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes"
    $ git push origin name-of-your-bugfix-or-feature

   Some tips for `good commit messages <https://gist.github.com/robertpainsi/b632364184e70900af4ab688decf6f53>`_.

7. `Submit a pull request <https://github.com/schuderer/mllaunchpad/compare>`_
   through the GitHub website: ``base: master <- compare: name-of-your-bugfix-or-feature``.
   Reference relevant GitHub issues by including their #<issue_number> in the
   pull request description.

Pull Request Guidelines
------------------------------------------------------------------------------

Before you submit a pull request, check that it meets these guidelines:

0. Make sure you have checked that it is not a duplicate, and it should
   be an attempt to solve a issue on GitHub. If no such issue exists, it is
   never a bad idea to create one first. This offers the chance
   to discuss the proposed change you propose with maintainers and
   other users before doing the actual work.
1. The pull request should include tests.
2. If the pull request adds or changes functionality, the docs should be updated.
   Update and add docstrings as needed, and update the ``docs/usage.rst``, and
   if it's a major addition, the ``README.rst``. List your contribution in
   the ``Unreleased`` section of ``CHANGELOG.rst``.
3. The pull request should work for Python 3.6 and 3.7.
   Check https://travis-ci.org/schuderer/mllaunchpad/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips and Troubleshooting
------------------------------------------------------------------------------
If installing the development requirements (``pip install -r requirements/dev.txt``)
fails, try to run the command again.

To run a subset of tests::

  $ pytest tests.test_module_testing_your_changes

If on step 3, you get an error creating the virtual environment
and are on an Anaconda,
installation, you might need to update conda and
then python before being able to create the virtual environment::

  $ conda update -n base -c defaults conda
  $ conda update python

On step 5: When editing documentation, it is handy to see your edits reflected
in the docs on-the-fly::

  $ nox -s docs -- monitor

Deploying
------------------------------------------------------------------------------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in ``CHANGELOG.rst``).
Then run::

$ bumpversion patch # possible: major / minor / patch
$ git push
$ git push --tags

Travis will then deploy to PyPI if tests pass.
