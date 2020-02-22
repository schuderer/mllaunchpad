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
min_coverage = "3"  # TODO: get to >= 90%


@nox.session(name="format", python=my_py_ver)
def code_formatting(session):
    """Run code reformatter"""
    session.install("black")
    session.run("black", "-l", max_line_length, *autoformat)


@nox.session(python=my_py_ver)
def lint(session):
    """Run code style checker"""
    session.install("flake8", "flake8-import-order", "black")
    session.run("black", "-l", max_line_length, "--check", *autoformat)
    session.run(
        "flake8", "--max-line-length=" + max_line_length, package_name, "tests"
    )


# @nox.parametrize("django", ["1.9", "2.0"])
# In Travis-CI: session selected via env vars
@nox.session(python=["3.6", my_py_ver])
def tests(session):
    """Run the unit test suite"""
    session.install("-r", "requirements/test.txt")
    session.run("pytest", "tests", "--quiet")


@nox.session(python=my_py_ver)
def coverage(session):
    """Run the unit test suite and check coverage"""
    session.install("-r", "requirements/test.txt")
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
    session.install("-r", "requirements/docs.txt")

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
