import os
from sys import platform
import nox

# Intro to Nox: https://www.youtube.com/watch?v=P3dY3uDmnkU
# Example (also used with Travis CI):
# https://github.com/theacodes/nox/blob/master/noxfile.py

ON_TRAVIS_CI = os.environ.get("TRAVIS")

package_name = "mllaunchpad"
my_py_ver = "3.7"
autoformat = [package_name, "tests", "noxfile.py", "setup.py"]
max_line_length = "79"
min_coverage = "30"  # TODO: get to >= 90%

# Skip "tests-3.7" by default as they are included in "coverage"
nox.options.sessions = ["format", "lint", "tests-3.6", "coverage", "docs"]

# TODO: Auto-parametrize dependencies from setup.py (regular mega-dep-check):
# 1. loop over setup.cfg's "install_requires":
# 1a. get available versions of all dependencies
# pip install pandas==givemeallversions
# Could not find a version that satisfies the requirement pandas==givemeallversions (from versions: 0.1, 0.2b0, 0.2b1, 0.2, 0.3.0b0, 0.3.0b2, 0.3.0, 0.4.0, 0.4.1, 0.4.2, 0.4.3, 0.5.0, 0.6.0, 0.6.1, 0.7.0rc1, 0.7.0, 0.7.1, 0.7.2, 0.7.3, 0.8.0rc1, 0.8.0rc2, 0.8.0, 0.8.1, 0.9.0, 0.9.1, 0.10.0, 0.10.1, 0.11.0, 0.12.0, 0.13.0, 0.13.1, 0.14.0, 0.14.1, 0.15.0, 0.15.1, 0.15.2, 0.16.0, 0.16.1, 0.16.2, 0.17.0, 0.17.1, 0.18.0, 0.18.1, 0.19.0rc1, 0.19.0, 0.19.1, 0.19.2, 0.20.0rc1, 0.20.0, 0.20.1, 0.20.2, 0.20.3, 0.21.0rc1, 0.21.0, 0.21.1, 0.22.0, 0.23.0rc2, 0.23.0, 0.23.1, 0.23.2, 0.23.3, 0.23.4, 0.24.0rc1, 0.24.0, 0.24.1, 0.24.2, 0.25.0rc0, 0.25.0, 0.25.1, 0.25.2, 0.25.3, 1.0.0rc0, 1.0.0, 1.0.1)
# 1b. get two newest major versions, or if only one, two newest minor versions
# 2. @nox.session(python=["3.6", my_py_ver])
#    @nox.parametrize('pandas', ['1.0.1', '0.25.3'])  # somehow do this in loop
#    ...
#    @nox.parametrize('flask', ['1.1.1', '0.12.5'])
#    def megatests(session, **dep_versions):
#        """Check recent versions of dependencies for compatibility"""
#        for dep, ver in dep_versions.items():
#           session.install(f'dep=={ver}')
#        ... install and carry out tests


@nox.session(name="format", python=my_py_ver)
def format_code(session):
    """Run code reformatter"""
    session.install("black")
    session.run("black", "-l", max_line_length, *autoformat)


@nox.session(python=my_py_ver)
def lint(session):
    """Run code style and vulnerability checkers"""
    session.install("flake8", "flake8-import-order", "black", "bandit")
    session.run("black", "-l", max_line_length, "--check", *autoformat)
    session.run(
        "flake8", "--max-line-length=" + max_line_length, package_name, "tests"
    )
    session.run("bandit", "-qr", "mllaunchpad", "noxfile.py", "setup.py")


# In Travis-CI: session selected via env vars
@nox.session(python=["3.6", my_py_ver])
def tests(session):
    """Run the unit test suite"""
    session.install("-e", ".[test]")
    session.run("pytest", "tests", "--quiet")


@nox.session(python=my_py_ver)
def coverage(session):
    """Run the unit test suite and check coverage"""
    session.install("-e", ".[test]")
    pytest_args = ["pytest", "tests", "--quiet"]
    session.run(
        *pytest_args,
        "--cov=" + package_name,
        "--cov-config",
        ".coveragerc",
        "--cov-report=",  # No coverage report
    )
    session.run(
        "coverage", "report", "--fail-under=" + min_coverage, "--show-missing"
    )
    if ON_TRAVIS_CI:
        session.install("coveralls")
        session.run("coveralls")
    session.run("coverage", "erase")


@nox.session(python=my_py_ver)
def docs(session):
    if platform == "win32" or platform == "cygwin":
        cmdc = ["cmd", "/c"]  # Needed for calling builtin commands
        session.run(*cmdc, "DEL", "/S", "/Q", "docs\\_build", external=True)
        session.run(*cmdc, "DEL", "/S", "/Q", "docs\\generated", external=True)
        session.run(*cmdc, "DEL", "/Q", "docs\\modules.rst", external=True)
        session.run(
            *cmdc, "DEL", "/Q", "docs\\" + package_name + ".rst", external=True
        )
    else:  # darwin, linux, linux2
        session.run("rm", "-rf", "docs/_build", external=True)
        session.run("rm", "-rf", "docs/generated", external=True)
        session.run("rm", "-f", "docs/modules.rst", external=True)
        session.run("rm", "-f", "docs/" + package_name + ".rst", external=True)
    # These two installs would suffice did we not have to create API-docs.
    # Then we also wouldn't have to use pip-installs here at all.
    # session.install("sphinx")
    # session.install(".")
    session.install("-e", ".[docs]")

    session.run(
        "sphinx-apidoc",
        "-M",  # put module documentation before submodule documentation
        "-T",  # don't generate table of contents file
        "-o",
        "docs",
        package_name,
        "*wsgi*",  # exclude_patterns doesn't seem to work
    )
    sphinx_args = [
        "-W",  # turn warnings into errors
        "-b",  # use builder: html
        "html",
        "docs",
        "docs/_build",
    ]
    if "monitor" in session.posargs:  # more explicit than session.interactive
        session.install("sphinx-autobuild")
        session.run("sphinx-autobuild", *sphinx_args)
    else:
        session.run("sphinx-build", *sphinx_args)
