#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mllaunchpad.yaml_loader module."""

# Stdlib imports
from unittest import mock

# Third party
import yaml

# Application imports
import mllaunchpad.yaml_loader as yloader

test_file_yaml = b"""
    dbms: !include test
     """
test = b"""
    xob10:
        type: oracle
    """


@mock.patch(
    "builtins.open", new_callable=mock.mock_open, read_data=test_file_yaml
)
def test_yaml_include(mo):
    """Isolated test include sub config files."""

    mo.return_value.name = "./foobar.yml"
    mo2 = mock.mock_open(read_data=test)
    mo2.return_value.name = "test"
    handlers = (mo.return_value, mo2.return_value)
    mo.side_effect = handlers

    with open(test_file_yaml) as f:
        data = yaml.load(f, yloader.Loader)
        assert data["dbms"]["xob10"]["type"] == "oracle"
