#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mllaunchpad.config` module."""

# Stdlib imports
from unittest import mock

# Third-party imports
import pytest

# Application imports
import mllaunchpad.config as config

test_file_valid = b"""
blabla:
    - asdf
    - adfs

model:
  name: my_model

api:
  name: my_api
"""


def test_get_config():
    """Test Config loading."""
    mo = mock.mock_open(read_data=test_file_valid)
    mo.return_value.name = "./foobar.yml"
    with mock.patch(
        "%s.open" % config.__name__,
        mo,  # <-- use our mock variable here
        create=True,
    ):
        cfg = config.get_validated_config("lalala")
        assert cfg["api"]["name"] == "my_api"
        assert cfg["api"]["name"] == "my_api"


def test_get_config_default_warning(caplog):
    """Test Config loading."""
    mo = mock.mock_open(read_data=test_file_valid)
    mo.return_value.name = "./foobar.yml"
    with mock.patch(
        "%s.open" % config.__name__,
        mo,  # <-- use our mock variable here
        create=True,
    ):
        _ = config.get_validated_config()
        assert "not set".lower() in caplog.text.lower()


def test_get_config_invalid():
    """Test config validation."""
    test_file_invalid = b"""
    blabla:
        - asdf
        - adfs
    nomodel:
        name: bla

    api:
        name: bla
    """
    mo = mock.mock_open(read_data=test_file_invalid)
    mo.return_value.name = "./foobar.yml"
    with mock.patch(
        "%s.open" % config.__name__,
        mo,  # <-- use our mock variable here
        create=True,
    ):
        with pytest.raises(ValueError, match="does not contain"):
            _ = config.get_validated_config("lalala")


test = b"""

     xob10:
        type: oracle

     """
test_file_yaml = b"""

    dbms: !include test

    model:
        name: my_model

    api:
        name: my_api
    """


@mock.patch(
    "builtins.open", new_callable=mock.mock_open, read_data=test_file_yaml
)
def test_yaml_include(mo):
    """Test include sub config files."""

    mo.return_value.name = "./foobar.yml"
    mo2 = mock.mock_open(read_data=test)
    mo2.return_value.name = "test"
    handlers = (mo.return_value, mo2.return_value)
    mo.side_effect = handlers

    with mock.patch(
        "%s.open" % config.__name__,
        mo,  # <-- use our mock variable here
        create=True,
    ):
        cfg = config.get_validated_config("lalala")
        assert cfg["dbms"]["xob10"]["type"] == "oracle"
