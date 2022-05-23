# Stdlib imports
import os
from sys import platform
from zipfile import ZipFile

# Third-party imports
import nox


# Intro to Nox: https://www.youtube.com/watch?v=P3dY3uDmnkU
# Example (also used with Travis CI):
# https://github.com/theacodes/nox/blob/master/noxfile.py

ON_TRAVIS_CI = os.environ.get("TRAVIS")

package_name = "mllaunchpad"
my_py_ver = "3.8"
files_to_format = [package_name, "tests", "noxfile.py", "setup.py"]
max_line_length = "79"  # I don't want a pyproject.toml just for 'black'...
min_coverage = "90"

# Skip "tests-3.7" by default as they are included in "coverage"
nox.options.sessions = [
    "format",
    "lint",
    "tests-3.7",
    "tests-3.9",
    "coverage",
    "docs",
]

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
    # session.install("-e", ".[lint]")
    session.install(
        "isort==5.10.1", "seed-isort-config==2.2.0", "black==22.3.0"
    )
    session.run("seed-isort-config", success_codes=[0, 1])
    session.run("isort", *files_to_format)
    session.run("black", "-l", max_line_length, *files_to_format)


@nox.session(python=my_py_ver)
def lint(session):
    """Run code style and vulnerability checkers"""
    # session.install("-e", ".[lint]")  # so isort can detect everything automatically, but heavy install
    session.install(
        "mypy==0.950",
        "isort==5.10.1",
        "seed-isort-config==2.2.0",
        "black==22.3.0",
        "flake8==4.0.1",
        "flake8-isort==4.1.1",
        "bandit==1.7.4",
    )
    session.run("mypy", "--install-types", "--non-interactive", package_name)
    session.run("mypy", package_name)
    session.run("seed-isort-config", success_codes=[0, 1])
    session.run("black", "-l", max_line_length, "--check", *files_to_format)
    session.run(
        "flake8", "--max-line-length=" + max_line_length, *files_to_format
    )
    session.run("bandit", "-qr", *[f for f in files_to_format if f != "tests"])
    print(
        "If bandit shows warnings about being unable to find qualified names, they can be ignored. "
        "https://github.com/PyCQA/bandit/discussions/725"
    )


# In Travis-CI: session selected via env vars
@nox.session(python=["3.6", "3.7", my_py_ver, "3.9"])
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
    zip_file = os.path.join("docs", "_static", "examples.zip")
    api_rst_file = os.path.join("docs", "{}.rst".format(package_name))
    if platform == "win32" or platform == "cygwin":
        cmdc = ["cmd", "/c"]  # Needed for calling builtin commands
        session.run(*cmdc, "DEL", "/S", "/Q", "docs\\_build", external=True)
        session.run(*cmdc, "DEL", "/S", "/Q", "docs\\generated", external=True)
        session.run(*cmdc, "DEL", "/Q", "docs\\modules.rst", external=True)
        session.run(*cmdc, "DEL", "/Q", zip_file, external=True)
        session.run(*cmdc, "DEL", "/Q", api_rst_file, external=True)
    else:  # darwin, linux, linux2
        session.run("rm", "-rf", "docs/_build", external=True)
        session.run("rm", "-rf", "docs/generated", external=True)
        session.run("rm", "-f", "docs/modules.rst", external=True)
        session.run("rm", "-f", zip_file, external=True)
        session.run("rm", "-f", api_rst_file, external=True)
    # These two installs would suffice did we not have to create API-docs.
    # Then we also wouldn't have to use pip-installs here at all.
    # session.install("sphinx")
    # session.install(".")
    session.install("-e", ".[docs]")

    with ZipFile(zip_file, "w") as z:
        base_path = "examples/"
        exclude = set(("model_store", "__pycache__", ".DS_Store"))
        len_base = len(base_path)
        for file_dir, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                file_path = os.path.join(file_dir, file)
                if not any([e in file_path for e in exclude]):
                    z.write(file_path, file_path[len_base:])

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
