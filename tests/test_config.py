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
    with mock.patch("builtins.open", mo, create=True):
        cfg = config.get_validated_config("lalala")
        assert cfg["api"]["name"] == "my_api"
        assert cfg["api"]["name"] == "my_api"


def test_get_config_default_warning(caplog):
    """Test Config loading."""
    mo = mock.mock_open(read_data=test_file_valid)
    mo.return_value.name = "./foobar.yml"
    with mock.patch("builtins.open", mo, create=True):
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
    with mock.patch("builtins.open", mo, create=True):
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

    with mock.patch("builtins.open", mo, create=True):
        cfg = config.get_validated_config("lalala")
        assert cfg["dbms"]["xob10"]["type"] == "oracle"


api_version_deprecation_file = """
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
{}  # version: ... for mllp<1.0.0 deprecated; and for mllp>=1.0.0 exception
"""


@pytest.mark.parametrize(
    "version, api_ver, deprecation_expected",
    [("0.99.99", "", False), ("0.99.99", "    version: 0.1.1", True)],
)
def test_config_api_version_deprecation_warning(
    version, api_ver, deprecation_expected
):
    """api:version should raise deprecation warning for mllaunchpad < 1.0"""
    test_file = api_version_deprecation_file.format(api_ver).encode("utf-8")
    mo = mock.mock_open(read_data=test_file)
    mo.return_value.name = "./foobar.yml"
    with mock.patch("builtins.open", mo, create=True):
        with mock.patch.object(mllaunchpad, "__version__", new=version):
            if deprecation_expected:
                with pytest.warns(DeprecationWarning):
                    _ = config.get_validated_config("lalala")
            else:
                with pytest.warns(None) as warnings:
                    _ = config.get_validated_config("lalala")
                assert not warnings


@pytest.mark.parametrize(
    "version, api_ver, deprecation_expected",
    [
        ("1.11.11", "", False),
        ("1.11.11", "    version: 0.1.1", True),
        ("2.11.11", "", False),
        ("2.11.11", "    version: 0.1.1", True),
    ],
)
def test_config_api_version_deprecation_error(
    version, api_ver, deprecation_expected
):
    """api:version should raise ValueError for mllp>=1.0"""
    test_file = api_version_deprecation_file.format(api_ver).encode("utf-8")
    mo = mock.mock_open(read_data=test_file)
    mo.return_value.name = "./foobar.yml"
    with mock.patch("builtins.open", mo, create=True):
        with mock.patch.object(mllaunchpad, "__version__", new=version):
            if deprecation_expected:
                with pytest.raises(ValueError, match="not allowed"):
                    _ = config.get_validated_config("lalala")
            else:
                _ = config.get_validated_config("lalala")
