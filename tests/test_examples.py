"""Tests for modules inside the `examples` directory."""

# Stdlib imports
import os
import sys
from unittest import mock

# Third-party imports
import pandas as pd
import pytest


impala_dbapi_mock = mock.MagicMock()
sys.modules["impala.dbapi"] = impala_dbapi_mock
import examples.impala_datasource as imp  # isort:skip # noqa: E402

del sys.modules["impala.dbapi"]


@pytest.fixture()
def impaladatasource_cfg_and_data():
    cfg = {
        "type": "dbms.my_connection",
        "query": "blabla",
        "tags": ["train"],
    }
    dbms_cfg = {
        "type": "impala",
        "host": "host.example.com",
        "port": 1251,
        "database": "my_db",
        "kerberos_service_name": "impala",
        "auth_mechanism": "GSSAPI",
        "use_ssl": "true",
    }
    return cfg, dbms_cfg, pd.DataFrame({"a": [1, 2, 3], "b": [3, 4, 5]})


@mock.patch("{}.pd.read_sql".format(imp.__name__))
def test_impaladatasource_df(pd_read, impaladatasource_cfg_and_data):
    """ImpalaDataSource should connect, read dataframe and return it unaltered."""
    cfg, dbms_cfg, data = impaladatasource_cfg_and_data
    impala_dbapi_mock.reset_mock()
    pd_read.return_value = data

    ds = imp.ImpalaDataSource("bla", cfg, dbms_cfg)
    df = ds.get_dataframe()

    pd.testing.assert_frame_equal(df, data)
    impala_dbapi_mock.connect.assert_called_once()
    pd_read.assert_called_once()


@mock.patch("{}.pd.read_sql".format(imp.__name__))
def test_impaladatasource_envvars(
    pd_read, impaladatasource_cfg_and_data, caplog
):
    """In initializing ImpalaDataSource with dbms-config containing _vars convention, should read vars"""
    cfg, dbms_cfg, data = impaladatasource_cfg_and_data
    dbms_cfg = {"password_var": "MY_PW_VAR"}

    # Missing env var logs warning, leaves params as-is
    impala_dbapi_mock.reset_mock()
    ds = imp.ImpalaDataSource("bla", cfg, dbms_cfg)
    ds.get_dataframe()
    assert "not set".lower() in caplog.text.lower()
    impala_dbapi_mock.connect.assert_called_once_with(**dbms_cfg)

    # Existing env var: parameter renamed and has value of env var.
    impala_dbapi_mock.reset_mock()
    env = {"MY_PW_VAR": "my_pass"}
    with mock.patch.dict(os.environ, env):
        ds = imp.ImpalaDataSource("bla", cfg, dbms_cfg)
        ds.get_dataframe()
        impala_dbapi_mock.connect.assert_called_once_with(
            password=env["MY_PW_VAR"]
        )


def test_impaladatasource_notimplemented(impaladatasource_cfg_and_data):
    cfg, dbms_cfg, _ = impaladatasource_cfg_and_data
    impala_dbapi_mock.reset_mock()

    ds = imp.ImpalaDataSource("bla", cfg, dbms_cfg)
    with pytest.raises(NotImplementedError):
        ds.get_dataframe(buffer=True)
    with pytest.raises(NotImplementedError, match="get_dataframe"):
        ds.get_raw()
