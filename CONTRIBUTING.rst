.. highlight:: shell

==============================================================================
Contributing
==============================================================================

Contributions are what keeps ML Launchpad growing and useful,
and they are greatly appreciated!
Every little bit helps, and credit will always be given.

Everyone is welcome to contribute, just be nice:
`Code of Conduct <https://mllaunchpad.readthedocs.io/en/latest/conduct.html>`_.

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

   Install the mllaunchpad package in editable mode. This includes its
   development requirements::

   $ pip install -e .[dev]

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally. Don't forget to create tests for
   your code.
   We use Google style, particularly `docstrings <https://google.github.io/styleguide/pyguide.html#381-docstrings>`_.

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
   only perform specific tests or checks. Run ``nox -l`` for a list of
   available sessions.

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
If installing the development requirements (``pip install -e .[dev]``)
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

On step 4 or 6, you might get a merge conflict on ``docs/_static/examples.zip``.
This file is generated automatically by nox when building the docs, and differences
lead to a different file. To resolve::

  $ git checkout --ours -- docs/_static/examples.zip
  $ git add docs/_static/examples.zip
  $ git commit

Then continue with what you wanted to do (in case of step 4, working on your code,
in case of step 6, pushing).

Deploying
------------------------------------------------------------------------------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed and do the following:

1. Decide on the new version number (e.g. ``2.1.23``, use semantic versioning).
2. Create a new branch to contain the release-related changes.
3. Make sure ``CHANGELOG.rst`` is complete and move all unreleased changes
   under a new header for this version.
4. Change the line ``version = ...`` in ``setup.cfg`` to the new version number.
5. Run ``nox`` again to make sure you did not break anything.
6. Commit and push the changes and create a pull request.
7. Modify/correct things in the PR to your heart's content, and when satisfied,
   merge it to ``master``.
8. On GitHub, create a draft release with a tag name like e.g. ``v2.1.23``,
   at target ``master``, and a name like e.g. ``Release 2.1.23``.
9. Get the doc's changes and paste them into the description (make them look nice).
10. Publish the release.
11. Check that Travis CI deployed the release to PyPI successfully.

Alternatively, you can also release ``mllaunchpad`` with these commands
(assuming you have already committed your version and changelog changes)::

  $ git tag -a v2.1.23 -m "Bump version to v2.1.23"
  $ git push
  $ git push --tags

In either case, Travis-CI will then deploy to PyPI if tests pass.
