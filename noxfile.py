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


# For details to use tox (or nox, in extension) with pipenv, see:
# https://docs.pipenv.org/en/latest/advanced/#tox-automation-project
def install_requirements(session, dev=True, safety_check=True):
    session.install("pipenv")
    pipenv_args = [
        "--bare",
        "install",
        "--skip-lock"  # 'soft' requirements (for libraries)
        # '--deploy'  # use for applications (freezed reqs), not libraries, gives error if Pipfile not in sync with Pipfile.lock
    ]
    if dev:
        pipenv_args.append("--dev")
    # Fails if Pipfile.lock is out of date, instead of generating a new one:
    session.run("pipenv", *pipenv_args)

    if safety_check:
        session.run("pipenv", "check")

    # # Now that --deploy ensured that Pipfile.lock is current and
    # # we checked for known vulnerabilities, generate requirements.txt:
    # session.run('pipenv', 'lock', '-r', '>requirements.txt')
    # # Install requirements.txt:
    # session.install('-r', 'requirements.txt')


@nox.session(python=my_py_ver)
def format(session):
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
@nox.session(python=["2.7", "3.5", "3.6", my_py_ver])
def tests(session):
    """Run the unit test suite"""
    # already part of dev-Pipfile
    # session.install('pytest', 'pytest-cov')
    safety_check = "safety" in session.posargs
    install_requirements(session, safety_check=safety_check)
    # session.install('-e', '.')  # we're testing a package
    # session.run('pipenv', 'install', '-e', '.')
    pytest_args = ["pipenv", "run", "pytest", "tests", "--quiet"]
    session.run(*pytest_args)


@nox.session(python=my_py_ver)
def coverage(session):
    """Run the unit test suite and check coverage"""
    safety_check = "safety" in session.posargs
    install_requirements(session, safety_check=safety_check)
    pytest_args = ["pipenv", "run", "pytest", "tests", "--quiet"]
    session.run(
        *pytest_args,
        "--cov=" + package_name,
        "--cov=agents",
        "--cov-config",
        ".coveragerc",
        "--cov-report=",  # No coverage report
    )
    session.install("coverage", "coveralls")
    session.run(
        "coverage", "report", "--fail-under=" + min_coverage, "--show-missing"
    )
    if ON_TRAVIS_CI:
        session.run("coveralls")
    session.run("coverage", "erase")


@nox.session(python=my_py_ver)
def docs(session):
    if platform == "win32" or platform == "cygwin":
        session.run("rmdir", "/S", "docs\\_build", external=True)
        session.run("rmdir", "/S", "docs\\_build", external=True)
        session.run("del", "docs\\modules.rst", external=True)
        session.run("del", "docs\\" + package_name + ".rst", external=True)
        session.run("del", "docs\\requirements.txt", external=True)
    else:  # darwin, linux, linux2
        session.run("rm", "-rf", "docs/_build", external=True)
        session.run("rm", "-rf", "docs/generated", external=True)
        session.run("rm", "-f", "docs/modules.rst", external=True)
        session.run("rm", "-f", "docs/" + package_name + ".rst", external=True)
        session.run("rm", "-f", "docs/requirements.txt", external=True)
    # These two installs would suffice did we not have to create requirements.
    # Then we also wouldn't have to use pipenv here at all.
    # session.install("sphinx")
    # session.install(".")
    install_requirements(session, dev=True, safety_check=False)
    session.chdir("docs")
    # TODO: get rid of Makefile and make.bat
    session.run("make", "reqs", external=True)
    session.chdir("..")

    session.run(
        "pipenv",
        "run",
        "sphinx-apidoc",
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
    if "monitor" in session.posargs:  # session.interactive:
        # session.run('pipenv', 'run', 'sphinx-autobuild', *sphinx_args)
        session.install("sphinx-autobuild")
        session.run("pipenv", "run", "sphinx-autobuild", *sphinx_args)
    else:
        # session.run('pipenv', 'run', 'sphinx-build', *sphinx_args)
        session.run("pipenv", "run", "sphinx-build", *sphinx_args)
