# Stdlib imports
import os
import sys
from io import BytesIO
from unittest import mock

# Third-party imports
import numpy as np
import pandas as pd
import pytest

# Project imports
import mllaunchpad.datasources as mllp_ds


@pytest.fixture()
def filedatasource_cfg_and_file():
    def _inner(file_type, dtypes=None):
        cfg = {
            "type": file_type,
            "path": "some_filename",
            "expires": 0,
            "tags": ["train"],
            "options": {},
        }
        return_tuple = None
        if file_type == "euro_csv":
            return_tuple = [
                cfg,
                b"""
"a";"b";"c";"d"
1,1;"ad";f,afd;1
2,3;"df";2.3,2
""",
            ]
        elif file_type == "csv":
            return_tuple = [
                cfg,
                b"""
"a","b","c","d"
1.1,"ad",f;afd,1
2.3,"df","2,3",2
""",
            ]
        else:
            return_tuple = cfg, b"Hello world!"
        if dtypes is not None:
            if file_type not in ["csv", "euro_csv"]:
                raise ValueError(
                    "Fixture's dtypes parameter only makes sense with CSVs"
                )
            cfg["dtypes_path"] = dtypes
            return_tuple.append(
                b"""columns,dtypes
a,str
b,str
c,str
d,float64
"""
            )
        return return_tuple

    return _inner


@pytest.mark.parametrize("file_type", ["csv", "euro_csv"])
def test_filedatasource_df(file_type, filedatasource_cfg_and_file):
    cfg, file = filedatasource_cfg_and_file(file_type)
    cfg["path"] = BytesIO(file)  # sort-of mocking the file for pandas to open
    ds = mllp_ds.FileDataSource("some_datasource", cfg)
    df = ds.get_dataframe()
    assert str(df["a"].dtype) == "float64"
    assert df["a"][1] == 2.3
    assert df["b"][0] == "ad"


@pytest.mark.parametrize("file_type", ["csv", "euro_csv"])
def test_filedatasource_df_dtypes(file_type, filedatasource_cfg_and_file):
    cfg, file, dtfile = filedatasource_cfg_and_file(
        file_type, dtypes="some_filename.dtypes"
    )
    cfg["path"] = BytesIO(file)  # sort-of mocking the file for pandas to open
    print(cfg["dtypes_path"])
    cfg["dtypes_path"] = BytesIO(dtfile)
    print(cfg["dtypes_path"])
    ds = mllp_ds.FileDataSource("some_datasource", cfg)
    df = ds.get_dataframe()
    assert str(df["a"].dtype) == "object"
    assert str(df["d"].dtype) == "float64"


def test_filedatasource_df_chunksize(filedatasource_cfg_and_file):
    cfg, file = filedatasource_cfg_and_file("csv")
    cfg["path"] = BytesIO(file)  # sort-of mocking the file for pandas to open
    ds = mllp_ds.FileDataSource("bla", cfg)
    df_iter = ds.get_dataframe(chunksize=1)
    df1, df2 = df_iter
    assert not isinstance(df_iter, pd.DataFrame)
    assert isinstance(df1, pd.DataFrame)
    assert isinstance(df2, pd.DataFrame)


@pytest.mark.parametrize("file_type", ["text_file", "binary_file"])
def test_filedatasource_raw(file_type, filedatasource_cfg_and_file):
    cfg, file = filedatasource_cfg_and_file(file_type)
    mo = mock.mock_open(read_data=file)
    mo.return_value.name = "./foobar"
    with mock.patch("builtins.open", mo, create=True):
        ds = mllp_ds.FileDataSource("bla", cfg)
        raw = ds.get_raw()
        if isinstance(raw, bytes):
            assert raw == b"Hello world!"
        elif isinstance(raw, str):
            assert raw == "Hello world!"
        else:
            assert False  # Unsupported type


def test_filedatasource_notimplemented(filedatasource_cfg_and_file):
    cfg, _ = filedatasource_cfg_and_file("csv")
    ds = mllp_ds.FileDataSource("bla", cfg)
    with pytest.raises(NotImplementedError):
        ds.get_dataframe(params={"a": "hallo"})
    with pytest.raises(TypeError, match="get_dataframe"):
        ds.get_raw()

    cfg, _ = filedatasource_cfg_and_file("text_file")
    ds = mllp_ds.FileDataSource("bla", cfg)
    with pytest.raises(NotImplementedError):
        ds.get_raw(params={"a": "hallo"})
    with pytest.raises(NotImplementedError):
        ds.get_raw(chunksize=5)
    with pytest.raises(TypeError, match="get_raw"):
        ds.get_dataframe()

    cfg["type"] = "sausage"
    with pytest.raises(TypeError, match="file type"):
        mllp_ds.FileDataSource("bla", cfg)


@pytest.fixture()
def filedatasink_cfg_and_data():
    def _inner(file_type, options=None, **extra):
        options = {} if options is None else options
        cfg = {
            "type": file_type,
            "path": "some_filename",
            "tags": ["train"],
            "options": options,
        }
        for key, value in extra.items():
            cfg[key] = value

        if file_type == "text_file":
            return cfg, "Hello world!"
        elif file_type == "binary_file":
            return cfg, b"Hello world!"
        else:
            return (
                cfg,
                pd.DataFrame(
                    {
                        "a": [1, 2, 3],
                        "b": [3, 4, 5],
                        "c": ["10-1993", "11-1996", "12-2012"],
                    }
                ),
            )

    return _inner


@pytest.mark.parametrize(
    "file_type, to_csv_params",
    [
        ("csv", {"index": False}),
        ("euro_csv", {"sep": ";", "decimal": ",", "index": False}),
    ],
)
@mock.patch("pandas.DataFrame.to_csv")
def test_filedatasink_df(
    to_csv_mock, file_type, to_csv_params, filedatasink_cfg_and_data
):
    cfg, data = filedatasink_cfg_and_data(file_type)
    ds = mllp_ds.FileDataSink("some_datasink", cfg)
    ds.put_dataframe(data)
    to_csv_mock.assert_called_once_with(cfg["path"], **to_csv_params)


@pytest.mark.parametrize("file_type", ["csv", "euro_csv"])
@mock.patch("pandas.DataFrame.to_csv")
def test_filedatasink_df_dtypes(
    to_csv_mock, file_type, filedatasink_cfg_and_data
):
    cfg, data = filedatasink_cfg_and_data(
        file_type, dtypes_path="dtypes_example.dtypes"
    )
    ds = mllp_ds.FileDataSink("some_datasink", cfg)
    ds.put_dataframe(data)

    assert to_csv_mock.call_count == 2


@mock.patch("pandas.DataFrame.to_csv")
def test_filedatasink_df_options(to_csv_mock, filedatasink_cfg_and_data):
    options = {"index": True, "sep": "?"}
    cfg, data = filedatasink_cfg_and_data("csv", options=options)
    ds = mllp_ds.FileDataSink("bla", cfg)
    ds.put_dataframe(data)
    to_csv_mock.assert_called_once_with(cfg["path"], **options)


@pytest.mark.parametrize(
    "file_type, mode", [("text_file", "w"), ("binary_file", "wb")]
)
def test_filedatasink_raw(file_type, mode, filedatasink_cfg_and_data):
    cfg, data = filedatasink_cfg_and_data(file_type)
    mo = mock.mock_open()
    mo.return_value.name = "./foobar"
    with mock.patch("builtins.open", mo, create=True):
        ds = mllp_ds.FileDataSink("bla", cfg)
        ds.put_raw(data)
        if mode == "w":
            mo.assert_called_once_with(cfg["path"], mode, encoding="utf-8")
        else:
            mo.assert_called_once_with(cfg["path"], mode)


def test_filedatasink_notimplemented(filedatasink_cfg_and_data):
    cfg, data = filedatasink_cfg_and_data("csv")
    ds = mllp_ds.FileDataSink("bla", cfg)
    with pytest.raises(NotImplementedError):
        ds.put_dataframe(data, params={"a": "hallo"})
    with pytest.raises(NotImplementedError):
        ds.put_dataframe(data, chunksize=5)
    with pytest.raises(TypeError, match="put_dataframe"):
        ds.put_raw(data)

    cfg, data = filedatasink_cfg_and_data("text_file")
    ds = mllp_ds.FileDataSink("bla", cfg)
    with pytest.raises(NotImplementedError):
        ds.put_raw(data, params={"a": "hallo"})
    with pytest.raises(NotImplementedError):
        ds.put_raw(data, chunksize=5)
    with pytest.raises(TypeError, match="put_raw"):
        ds.put_dataframe(data)

    cfg["type"] = "sausage"
    with pytest.raises(TypeError, match="file type"):
        mllp_ds.FileDataSink("bla", cfg)


@mock.patch("os.makedirs")
@mock.patch("os.path.exists", return_value=False)
@mock.patch("pandas.DataFrame.to_csv")
def test_filedatasink_df_ensure_path(
    to_csv_mock, exists_mock, makedirs_mock, filedatasink_cfg_and_data
):
    cfg, data = filedatasink_cfg_and_data("csv")
    cfg["path"] = os.path.join("bla/foo", cfg["path"])
    ds = mllp_ds.FileDataSink("bla", cfg)
    ds.put_dataframe(data)
    exists_mock.assert_called_once()
    makedirs_mock.assert_called_once_with("bla/foo")


@mock.patch("os.makedirs")
@mock.patch("os.path.exists", return_value=True)
@mock.patch("pandas.DataFrame.to_csv")
def test_filedatasink_df_ensure_path_noexist(
    to_csv_mock, exists_mock, makedirs_mock, filedatasink_cfg_and_data
):
    cfg, data = filedatasink_cfg_and_data("csv")
    cfg["path"] = os.path.join("bla/foo", cfg["path"])
    ds = mllp_ds.FileDataSink("bla", cfg)
    ds.put_dataframe(data)
    exists_mock.assert_called_once()
    makedirs_mock.assert_not_called()


# OracleDataSource


@pytest.fixture()
def oracledatasource_cfg_and_data():
    def _inner(options=None):
        options = {} if options is None else options
        cfg = {
            "type": "dbms.my_connection",
            "query": "blabla",
            "tags": ["train"],
            "options": options,
        }
        dbms_cfg = {
            "type": "oracle",
            "host": "host.example.com",
            "port": 1251,
            "user_var": "MY_USER_ENV_VAR",
            "password_var": "MY_PW_ENV_VAR",
            "service_name": "servicename.example.com",
            "options": options,
        }
        return cfg, dbms_cfg, pd.DataFrame({"a": [1, 2, 3], "b": [3, 4, 5]})

    return _inner


@mock.patch("pandas.read_sql")
@mock.patch(
    "{}.get_user_pw".format(mllp_ds.__name__), return_value=("foo", "bar")
)
def test_oracledatasource_df(user_pw, pd_read, oracledatasource_cfg_and_data):
    """OracleDataSource should connect, read dataframe and return it unaltered."""
    cfg, dbms_cfg, data = oracledatasource_cfg_and_data()
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock
    pd_read.return_value = data

    ds = mllp_ds.OracleDataSource("bla", cfg, dbms_cfg)
    df = ds.get_dataframe()

    pd.testing.assert_frame_equal(df, data)
    ora_mock.connect.assert_called_once()
    pd_read.assert_called_once()

    del sys.modules["cx_Oracle"]


@mock.patch("pandas.read_sql")
@mock.patch(
    "{}.get_user_pw".format(mllp_ds.__name__), return_value=("foo", "bar")
)
def test_oracledatasource_df_chunksize(
    user_pw, pd_read, oracledatasource_cfg_and_data
):
    """OracleDataSource with chunksize should return generator."""
    cfg, dbms_cfg, full_data = oracledatasource_cfg_and_data()
    iter_data = [full_data.iloc[:2, :].copy(), full_data.iloc[2:, :].copy()]
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock
    pd_read.return_value = iter_data

    ds = mllp_ds.OracleDataSource("bla", cfg, dbms_cfg)
    df_gen = ds.get_dataframe(chunksize=2)

    for df, orig in zip(df_gen, iter_data):
        pd.testing.assert_frame_equal(df, orig)

    del sys.modules["cx_Oracle"]


@mock.patch(
    "{}.get_user_pw".format(mllp_ds.__name__), return_value=("foo", "bar")
)
def test_oracledatasource_notimplemented(
    user_pw, oracledatasource_cfg_and_data
):
    cfg, dbms_cfg, _ = oracledatasource_cfg_and_data()
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock

    ds = mllp_ds.OracleDataSource("bla", cfg, dbms_cfg)
    with pytest.raises(NotImplementedError, match="get_dataframe"):
        ds.get_raw()

    del sys.modules["cx_Oracle"]


@pytest.mark.parametrize(
    "values, expected",
    [
        (
            pd.DataFrame(
                {
                    "a": [1, 2, 3, 4, 5, 6, 7],
                    "b": [3, 2, 7, None, 5, 7, 3],
                    "c": [1, 6, np.nan, 5, 7, None, 0],
                }
            ),
            pd.DataFrame(
                {
                    "a": [1, 2, 3, 4, 5, 6, 7],
                    "b": [3, 2, 7, np.nan, 5, 7, 3],
                    "c": [1, 6, np.nan, 5, 7, np.nan, 0],
                }
            ),
        ),
        (
            pd.DataFrame(
                {
                    "a": [1, 2, "3", None, 5, 6, 7],
                    "b": [3, 2, 7, None, "4", 7, 3],
                    "c": [1, 6, np.nan, 5, 7, "0", 0],
                }
            ),
            pd.DataFrame(
                {
                    "a": [1, 2, "3", np.nan, 5, 6, 7],
                    "b": [3, 2, 7, np.nan, "4", 7, 3],
                    "c": [1, 6, np.nan, 5, 7, "0", 0],
                }
            ),
        ),
        (
            pd.DataFrame(
                {
                    "a": [1, 2, "x", 4, 5, 6, 7],
                    "b": [3, 2, 7, None, "y", 7, 3],
                    "c": [1, 6, np.nan, 5, 7, "z", 0],
                }
            ),
            pd.DataFrame(
                {
                    "a": [1, 2, "x", 4, 5, 6, 7],
                    "b": [3, 2, 7, np.nan, "y", 7, 3],
                    "c": [1, 6, np.nan, 5, 7, "z", 0],
                }
            ),
        ),
    ],
)
@mock.patch("pandas.read_sql")
@mock.patch(
    "{}.get_user_pw".format(mllp_ds.__name__), return_value=("foo", "bar")
)
def test_oracledatasource_regression_nas_issue86(
    user_pw, pd_read, values, expected, oracledatasource_cfg_and_data
):
    """
    OracleDataSource should connect, read dataframe and return it unaltered
    with the exception of None values --> they should be converted to np.nan.
    """
    cfg, dbms_cfg, _ = oracledatasource_cfg_and_data()
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock
    pd_read.return_value = values

    ds = mllp_ds.OracleDataSource("bla", cfg, dbms_cfg)
    df = ds.get_dataframe()

    pd.testing.assert_frame_equal(df, expected)
    # assert df == expected
    ora_mock.connect.assert_called_once()
    pd_read.assert_called_once()

    del sys.modules["cx_Oracle"]


@mock.patch("pandas.DataFrame.to_sql")
@mock.patch(
    "{}.get_user_pw".format(mllp_ds.__name__), return_value=("foo", "bar")
)
def test_oracledatasink_df(user_pw, df_write, oracledatasource_cfg_and_data):
    cfg, dbms_cfg, data = oracledatasource_cfg_and_data()
    del cfg["query"]
    cfg["table"] = "blabla"
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock
    df_write.return_value = data

    ds = mllp_ds.OracleDataSink("bla", cfg, dbms_cfg)
    ds.put_dataframe(data)

    ora_mock.connect.assert_called_once()
    df_write.assert_called_once()

    del sys.modules["cx_Oracle"]


@mock.patch(
    "{}.get_user_pw".format(mllp_ds.__name__), return_value=("foo", "bar")
)
def test_oracledatasink_notimplemented(user_pw, oracledatasource_cfg_and_data):
    cfg, dbms_cfg, data = oracledatasource_cfg_and_data()
    del cfg["query"]
    cfg["table"] = "blabla"
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock

    ds = mllp_ds.OracleDataSink("bla", cfg, dbms_cfg)
    with pytest.raises(NotImplementedError):
        ds.put_dataframe(data, params={"a": "hallo"})
    with pytest.raises(NotImplementedError):
        ds.put_dataframe(data, chunksize=7)
    with pytest.raises(NotImplementedError, match="put_dataframe"):
        ds.put_raw(data)

    del sys.modules["cx_Oracle"]


# SqlDataSource


@mock.patch("os.environ.get")
def test_get_connection_args(env_get):
    """Should look up any _var-suffixed properties of the `options` subdict"""
    dbms_config = {
        "hello": "bla",
        "notlookedup_var": "NEVER_LOOKED_UP",
        "options": {
            "lookedup_var": "SOME_ENV_VAR",
            "notlookedup": "original_value",
        },
    }
    env_get.return_value = "replaced_value"
    assert mllp_ds.get_connection_args(dbms_config) == {
        "lookedup": "replaced_value",
        "notlookedup": "original_value",
    }


@mock.patch("os.environ.get")
def test_get_connection_args_no_options(env_get):
    """Return empty dict if there is no options subdict"""
    assert mllp_ds.get_connection_args({"no": "options dict"}) == {}

    dbms_config = {
        "hello": "bla",
        "notlookedup_var": "NEVER_LOOKED_UP",
        "options": {},
    }
    assert mllp_ds.get_connection_args(dbms_config) == {}
    env_get.assert_not_called()


@mock.patch("os.environ.get")
def test_get_connection_args_missing_env_var(env_get, caplog):
    """Warn if _var specified, but no env var present"""
    dbms_config = {
        "hello": "bla",
        "options": {
            "lookedup_var": "NONEXISTING_ENV_VAR",
            "notlookedup": "original_value",
        },
    }
    env_get.return_value = None
    assert mllp_ds.get_connection_args(dbms_config) == {
        "lookedup_var": "NONEXISTING_ENV_VAR",
        "notlookedup": "original_value",
    }
    assert "not set" in caplog.text.lower()


@pytest.fixture()
def sqldatasource_cfg_and_data():
    def _inner(options=None):
        options = {} if options is None else options
        cfg = {
            "type": "dbms.my_connection",
            "query": "blabla",
            "tags": ["train"],
            "options": options,
        }
        dbms_cfg = {
            "type": "sql",
            "connection_string": "bla+blu:host.example.com/?asdf=asfd",
            "port": 1234,
            "options": options,
        }
        return cfg, dbms_cfg, pd.DataFrame({"a": [1, 2, 3], "b": [3, 4, 5]})

    return _inner


@mock.patch("pandas.read_sql")
def test_sqldatasource_df(pd_read, sqldatasource_cfg_and_data):
    """SqlDataSource should connect, read dataframe and return it unaltered."""
    cfg, dbms_cfg, data = sqldatasource_cfg_and_data()
    sqla_mock = mock.MagicMock()
    sys.modules["sqlalchemy"] = sqla_mock
    pd_read.return_value = data

    ds = mllp_ds.SqlDataSource("bla", cfg, dbms_cfg)
    df = ds.get_dataframe()

    pd.testing.assert_frame_equal(df, data)
    sqla_mock.create_engine.assert_called_once_with(
        dbms_cfg["connection_string"], connect_args={}, port=1234
    )
    pd_read.assert_called_once()

    del sys.modules["sqlalchemy"]


@mock.patch("pandas.read_sql")
def test_sqldatasource_df_chunksize(pd_read, sqldatasource_cfg_and_data):
    """OracleDataSource with chunksize should return generator."""
    cfg, dbms_cfg, full_data = sqldatasource_cfg_and_data()
    iter_data = [full_data.iloc[:2, :].copy(), full_data.iloc[2:, :].copy()]
    sqla_mock = mock.MagicMock()
    sys.modules["sqlalchemy"] = sqla_mock
    pd_read.return_value = iter_data

    ds = mllp_ds.SqlDataSource("bla", cfg, dbms_cfg)
    df_gen = ds.get_dataframe(chunksize=2)

    for df, orig in zip(df_gen, iter_data):
        pd.testing.assert_frame_equal(df, orig)

    del sys.modules["sqlalchemy"]


def test_sqldatasource_notimplemented(sqldatasource_cfg_and_data):
    cfg, dbms_cfg, _ = sqldatasource_cfg_and_data()
    sqla_mock = mock.MagicMock()
    sys.modules["sqlalchemy"] = sqla_mock

    ds = mllp_ds.SqlDataSource("bla", cfg, dbms_cfg)
    with pytest.raises(NotImplementedError, match="get_dataframe"):
        ds.get_raw()

    del sys.modules["sqlalchemy"]


def test_sqldatasource_url_instead_of_connection_string(
    sqldatasource_cfg_and_data,
):
    cfg, dbms_cfg, _ = sqldatasource_cfg_and_data()
    dbms_cfg["url"] = dbms_cfg["connection_string"]
    del dbms_cfg["connection_string"]
    sqla_mock = mock.MagicMock()
    sys.modules["sqlalchemy"] = sqla_mock

    mllp_ds.SqlDataSource("bla", cfg, dbms_cfg)
    sqla_mock.create_engine.assert_called_once_with(
        dbms_cfg["url"], connect_args={}, port=1234
    )

    del sys.modules["sqlalchemy"]


def test_sqldatasource_double_url(sqldatasource_cfg_and_data):
    cfg, dbms_cfg, _ = sqldatasource_cfg_and_data()
    dbms_cfg["url"] = "the presence of `url` conflicts with connection_string"
    sqla_mock = mock.MagicMock()
    sys.modules["sqlalchemy"] = sqla_mock

    with pytest.raises(ValueError, match="connection_string"):
        mllp_ds.SqlDataSource("bla", cfg, dbms_cfg)

    del sys.modules["sqlalchemy"]


@mock.patch("pandas.DataFrame.to_sql")
def test_sqldatasink_df(df_write, sqldatasource_cfg_and_data):
    cfg, dbms_cfg, data = sqldatasource_cfg_and_data()
    del cfg["query"]
    cfg["table"] = "blabla"
    sqla_mock = mock.MagicMock()
    sys.modules["sqlalchemy"] = sqla_mock
    df_write.return_value = data

    ds = mllp_ds.SqlDataSink("bla", cfg, dbms_cfg)
    ds.put_dataframe(data)

    sqla_mock.create_engine.assert_called_once()
    df_write.assert_called_once()

    del sys.modules["sqlalchemy"]


def test_sqldatasink_notimplemented(sqldatasource_cfg_and_data):
    cfg, dbms_cfg, data = sqldatasource_cfg_and_data()
    del cfg["query"]
    cfg["table"] = "blabla"
    sqla_mock = mock.MagicMock()
    sys.modules["sqlalchemy"] = sqla_mock

    ds = mllp_ds.SqlDataSink("bla", cfg, dbms_cfg)
    with pytest.raises(NotImplementedError):
        ds.put_dataframe(data, params={"a": "hallo"})
    with pytest.raises(NotImplementedError):
        ds.put_dataframe(data, chunksize=7)
    with pytest.raises(NotImplementedError, match="put_dataframe"):
        ds.put_raw(data)

    del sys.modules["sqlalchemy"]
