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
    with mock.patch(
        "%s.open" % config.__name__,
        mock.mock_open(read_data=test_file_valid),
        create=True,
    ):
        cfg = config.get_validated_config("lalala")
        assert cfg["api"]["name"] == "my_api"
        assert cfg["api"]["name"] == "my_api"


def test_get_config_default_warning(caplog):
    """Test Config loading."""
    with mock.patch(
        "%s.open" % config.__name__,
        mock.mock_open(read_data=test_file_valid),
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
    with mock.patch(
        "%s.open" % config.__name__,
        mock.mock_open(read_data=test_file_invalid),
        create=True,
    ):
        with pytest.raises(ValueError, match="does not contain"):
            _ = config.get_validated_config("lalala")
