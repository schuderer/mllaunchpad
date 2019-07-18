#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst", encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst", encoding="utf-8") as history_file:
    history = history_file.read()

requirements = ["flask", "flask-restful", "ramlfications", "dill", "pandas"]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="Andreas Schuderer",
    author_email="pypi@schuderer.net",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved "
        ":: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        # "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Easily make Machine Learning models "
    "available as REST API. Lightweight model "
    "life cycle management.",
    entry_points={"console_scripts": ["mllaunchpad=mllaunchpad.cli:main"]},
    python_requires=">=2.7,!=3.0.*,!=3.1.*,,!=3.2.*,!=3.3.*,!=3.4.*",
    install_requires=requirements,
    license="GNU Lesser General Public License v3",
    long_description=readme + "\n\n" + history,
    # long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="mllaunchpad",
    name="mllaunchpad",
    packages=find_packages(include=["mllaunchpad"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/schuderer/mllaunchpad",
    version="0.0.1",
    zip_safe=False,
)
