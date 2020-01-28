#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst", encoding="utf-8") as readme_file:
    readme = readme_file.read()

requirements = [
    "flask",
    "flask-restful",
    "ramlfications",
    "dill",
    "pandas",
    "pyyaml",
]

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
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        # "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        # "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Deploy Machine Learning Solutions with Ease",
    entry_points={"console_scripts": ["mllaunchpad=mllaunchpad.cli:main"]},
    python_requires=">=3.6",
    install_requires=requirements,
    license="Apache License, Version 2.0",
    long_description=readme,  # + "\n\n" + history,
    long_description_content_type="text/x-rst",
    # long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="mllaunchpad",
    name="mllaunchpad",
    packages=find_packages(include=["mllaunchpad"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/schuderer/mllaunchpad",
    version="0.0.7",
    zip_safe=False,
)
