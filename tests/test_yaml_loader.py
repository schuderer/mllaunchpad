#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mllaunchpad.config` module."""

# Stdlib imports
from unittest import mock

# Application imports
import mllaunchpad.yaml_loader as yloader
import yaml

test_file_yaml = b"""
    dbms: !include test
     """
test = b"""
    xob10:
        type: oracle
    """


@mock.patch('__builtin__.open', new_callable=mock.mock_open, read_data=test_file_yaml)
def test_yaml_include(mo):
    """Test include sub config files."""

    handlers = (mo.return_value, mock.mock_open(read_data=test).return_value,)
    mo.side_effect = handlers
    with open("test_file_yaml") as f:
        data = yaml.load(f, yloader.Loader)
        assert data['dbms']['xob10']['type'] == 'oracle'
