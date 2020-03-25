"""Tests for `mllaunchpad.config` module."""

# Stdlib imports
from unittest import mock

# Third-party imports
import pytest

# Project imports
import mllaunchpad
import mllaunchpad.config as config


test_file_valid = b"""
blabla:
    - asdf
    - adfs

model_store:
    location: asdfasdf

model:
  name: my_model
  version: '0.1.2'
  module: my_model

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

    model:
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
        with pytest.raises(ValueError, match="Missing key"):
            _ = config.get_validated_config("lalala")


test = b"""

     xob10:
        type: oracle

     """
test_file_yaml = b"""

    dbms: !include test

    model_store:
        location: asdfasdf

    model:
        name: my_model
        version: '0.1.2'
        module: my_model

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


def test_config_api_version_deprecation():
    test_file_deprecated = b"""
    blabla:
        - asdf
        - adfs

    model_store:
        location: asdfasdf

    model:
        name: bla
        version: 0.1.1
        module: asoeutnh

    api:
        name: bla
        version: 0.1.1  # deprecated; and for mllp>=1.0.0 exception
    """
    mo = mock.mock_open(read_data=test_file_deprecated)
    mo.return_value.name = "./foobar.yml"
    with mock.patch(
        "%s.open" % config.__name__,
        mo,  # <-- use our mock variable here
        create=True,
    ):
        if mllaunchpad.__version__ < "1.0.0":
            with pytest.warns(DeprecationWarning):
                _ = config.get_validated_config("lalala")
        else:
            with pytest.raises(ValueError, match="not allowed"):
                _ = config.get_validated_config("lalala")
