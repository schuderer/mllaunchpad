"""Tests for `mllaunchpad.resource` module."""

# Stdlib imports
import json
import os
import sys
from collections import OrderedDict
from io import BytesIO
from unittest import mock

# Third-party imports
import numpy as np
import pandas as pd
import pytest

# Project imports
from mllaunchpad import resource as r


# Test ModelStore

# fmt: off
@pytest.fixture()
def modelstore_config():
    return {
        "model_store": {
            "location": "./model_store",
        },
        "model": {
            "name": "IrisModel",
            "version": '0.0.2',
            "module": "tree_model",
            "train_options": {},
            "predict_options": {},
        },
    }
# fmt: on


@mock.patch("{}.os.path.exists".format(r.__name__), return_value=False)
@mock.patch("{}.os.makedirs".format(r.__name__))
def test_modelstore_create(makedirs, path_exists, modelstore_config):
    _ = r.ModelStore(modelstore_config)
    makedirs.assert_called_once_with(
        modelstore_config["model_store"]["location"]
    )

    path_exists.reset_mock()
    makedirs.reset_mock()
    path_exists.return_value = True
    _ = r.ModelStore(modelstore_config)
    assert not makedirs.called


@mock.patch("{}.os.path.exists".format(r.__name__), return_value=False)
@mock.patch("{}.os.makedirs".format(r.__name__))
@mock.patch("{}.shutil.copy".format(r.__name__))
def test_modelstore_dump(copy, makedirs, path_exists, modelstore_config):
    with mock.patch(
        "{}.open".format(r.__name__), mock.mock_open(), create=True
    ) as mo:
        ms = r.ModelStore(modelstore_config)
        ms.dump_trained_model(modelstore_config, {"hi": 1}, {"there": 2})

    model_conf = modelstore_config["model"]
    base_name = os.path.join(
        modelstore_config["model_store"]["location"],
        "{}_{}".format(model_conf["name"], model_conf["version"]),
    )
    calls = [
        mock.call("{}.pkl".format(base_name), "wb"),
        mock.call("{}.json".format(base_name), "w"),
    ]
    mo.assert_has_calls(calls, any_order=True)


@mock.patch("{}.pickle.load".format(r.__name__), return_value="pickle")
@mock.patch("{}.json.load".format(r.__name__), return_value={"json": 0})
def test_modelstore_load(json, pkl, modelstore_config):
    with mock.patch(
        "{}.open".format(r.__name__), mock.mock_open(), create=True
    ) as mo:
        ms = r.ModelStore(modelstore_config)
        ms.load_trained_model(modelstore_config["model"])

    model_conf = modelstore_config["model"]
    base_name = os.path.join(
        modelstore_config["model_store"]["location"],
        "{}_{}".format(model_conf["name"], model_conf["version"]),
    )
    calls = [
        mock.call("{}.pkl".format(base_name), "rb"),
        mock.call("{}.json".format(base_name), "r"),
    ]
    mo.assert_has_calls(calls, any_order=True)


@mock.patch(
    "{}.ModelStore._load_metadata".format(r.__name__),
    return_value={"metrics": {"a": 0}, "metrics_history": {"0123": {"a": 0}}},
)
@mock.patch("{}.ModelStore._dump_metadata".format(r.__name__))
def test_modelstore_update_model_metrics(dump, load, modelstore_config):
    new_metrics = {"a": 1}
    ms = r.ModelStore(modelstore_config)
    ms.update_model_metrics(modelstore_config["model"], new_metrics)
    load.assert_called_once()
    dump.assert_called_once()
    name, contents = dump.call_args[0]
    assert contents["metrics"] == new_metrics
    hist = contents["metrics_history"]
    assert len(hist) == 2
    del hist["0123"]
    assert hist.popitem()[1] == new_metrics


# Test DataSource caching

# fmt: off
@pytest.fixture()
def datasource_expires_config():
    def _res(expires):
        return {
            "type": "mock",
            "expires": expires,
            "tags": ["train"],
        }
    return _res
# fmt: on


class MockDataSource(r.DataSource):
    serves = ["mock"]

    def get_dataframe(self, arg_dict=None, buffer=False):
        cached = self._try_get_cached_df()
        if cached is not None:
            print("cached")
            return cached
        df = pd.DataFrame(arg_dict)
        self._cache_df_if_required(df)
        return df

    def get_raw(self, arg_dict=None, buffer=False):
        cached = self._try_get_cached_raw()
        if cached is not None:
            print("cached")
            return cached
        raw = arg_dict
        self._cache_raw_if_required(arg_dict)
        return raw


@pytest.mark.parametrize(
    "expires, expected_cached", [(0, False), (100000, True), (-1, True)]
)
def test_datasource_caching_df(
    expires, expected_cached, capsys, datasource_expires_config
):
    args = {"a": [1, 2, 3], "b": [3, 4, 5]}
    ds = MockDataSource("mock", datasource_expires_config(expires))

    # 1st DF read
    df = ds.get_dataframe(arg_dict=args)
    out, _ = capsys.readouterr()
    pd.testing.assert_frame_equal(df, pd.DataFrame(args))
    assert "cached" not in out

    # 2nd DF read
    df = ds.get_dataframe(arg_dict=args)
    out, _ = capsys.readouterr()
    pd.testing.assert_frame_equal(df, pd.DataFrame(args))
    assert ("cached" in out) == expected_cached

    # 3rd DF read
    df = ds.get_dataframe(arg_dict=args)
    out, _ = capsys.readouterr()
    pd.testing.assert_frame_equal(df, pd.DataFrame(args))
    assert ("cached" in out) == expected_cached


@pytest.mark.parametrize(
    "expires, expected_cached", [(0, False), (100000, True), (-1, True)]
)
def test_datasource_caching_raw(
    expires, expected_cached, capsys, datasource_expires_config
):
    args = {"a": [1, 2, 3], "b": [3, 4, 5]}
    ds = MockDataSource("mock", datasource_expires_config(expires))

    # 1st raw read
    raw = ds.get_raw(arg_dict=args)
    out, _ = capsys.readouterr()
    assert raw == args
    assert "cached" not in out

    # 2nd raw read
    raw = ds.get_raw(arg_dict=args)
    out, _ = capsys.readouterr()
    assert raw == args
    assert ("cached" in out) == expected_cached


# Test FileDataSource


@pytest.fixture()
def filedatasource_cfg_and_file():
    def _inner(file_type):
        cfg = {
            "type": file_type,
            "path": "blabla",
            "expires": 0,
            "tags": ["train"],
            "options": {},
        }
        if file_type == "euro_csv":
            return (
                cfg,
                b"""
"a";"b";"c"
1,1;"ad";f,afd
2,3;"df";2.3
""",
            )
        elif file_type == "csv":
            return (
                cfg,
                b"""
"a","b","c"
1.1,"ad",f;afd
2.3,"df","2,3"
""",
            )
        else:
            return cfg, b"Hello world!"

    return _inner


@pytest.mark.parametrize("file_type", ["csv", "euro_csv"])
def test_filedatasource_df(file_type, filedatasource_cfg_and_file):
    cfg, file = filedatasource_cfg_and_file(file_type)
    cfg["path"] = BytesIO(file)  # sort-of mocking the file for pandas to open
    ds = r.FileDataSource("bla", cfg)
    df = ds.get_dataframe()
    assert str(df["a"].dtype) == "float64"
    assert df["a"][1] == 2.3
    assert df["b"][0] == "ad"


@pytest.mark.parametrize("file_type", ["text_file", "binary_file"])
def test_filedatasource_raw(file_type, filedatasource_cfg_and_file):
    cfg, file = filedatasource_cfg_and_file(file_type)
    mo = mock.mock_open(read_data=file)
    mo.return_value.name = "./foobar"
    with mock.patch("builtins.open", mo, create=True):
        ds = r.FileDataSource("bla", cfg)
        raw = ds.get_raw()
        if isinstance(raw, bytes):
            assert raw == b"Hello world!"
        elif isinstance(raw, str):
            assert raw == "Hello world!"
        else:
            assert False  # Unsupported type


def test_filedatasource_notimplemented(filedatasource_cfg_and_file):
    cfg, _ = filedatasource_cfg_and_file("csv")
    ds = r.FileDataSource("bla", cfg)
    with pytest.raises(NotImplementedError):
        ds.get_dataframe(buffer=True)
    with pytest.raises(TypeError, match="get_dataframe"):
        ds.get_raw()

    cfg, _ = filedatasource_cfg_and_file("text_file")
    ds = r.FileDataSource("bla", cfg)
    with pytest.raises(NotImplementedError):
        ds.get_raw(buffer=True)
    with pytest.raises(TypeError, match="get_raw"):
        ds.get_dataframe()

    cfg["type"] = "sausage"
    with pytest.raises(TypeError, match="file type"):
        r.FileDataSource("bla", cfg)


# Test FileDataSink


@pytest.fixture()
def filedatasink_cfg_and_data():
    def _inner(file_type, options=None):
        options = {} if options is None else options
        cfg = {
            "type": file_type,
            "path": "blabla",
            "tags": ["train"],
            "options": options,
        }
        if file_type == "text_file":
            return cfg, "Hello world!"
        elif file_type == "binary_file":
            return cfg, b"Hello world!"
        else:
            return cfg, pd.DataFrame({"a": [1, 2, 3], "b": [3, 4, 5]})

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
    read_sql_mock, file_type, to_csv_params, filedatasink_cfg_and_data
):
    cfg, data = filedatasink_cfg_and_data(file_type)
    ds = r.FileDataSink("bla", cfg)
    ds.put_dataframe(data)
    read_sql_mock.assert_called_once_with(cfg["path"], **to_csv_params)


@mock.patch("pandas.DataFrame.to_csv".format(r.__name__))
def test_filedatasink_df_options(read_sql_mock, filedatasink_cfg_and_data):
    options = {"index": True, "sep": "?"}
    cfg, data = filedatasink_cfg_and_data("csv", options=options)
    ds = r.FileDataSink("bla", cfg)
    ds.put_dataframe(data)
    read_sql_mock.assert_called_once_with(cfg["path"], **options)


@pytest.mark.parametrize(
    "file_type, mode", [("text_file", "w"), ("binary_file", "wb")]
)
def test_filedatasink_raw(file_type, mode, filedatasink_cfg_and_data):
    cfg, data = filedatasink_cfg_and_data(file_type)
    mo = mock.mock_open()
    mo.return_value.name = "./foobar"
    with mock.patch("builtins.open", mo, create=True):
        ds = r.FileDataSink("bla", cfg)
        ds.put_raw(data)
        mo.assert_called_once_with(cfg["path"], mode)


def test_filedatasink_notimplemented(filedatasink_cfg_and_data):
    cfg, data = filedatasink_cfg_and_data("csv")
    ds = r.FileDataSink("bla", cfg)
    with pytest.raises(NotImplementedError):
        ds.put_dataframe(data, buffer=True)
    with pytest.raises(TypeError, match="put_dataframe"):
        ds.put_raw(data)

    cfg, data = filedatasink_cfg_and_data("text_file")
    ds = r.FileDataSink("bla", cfg)
    with pytest.raises(NotImplementedError):
        ds.put_raw(data, buffer=True)
    with pytest.raises(TypeError, match="put_raw"):
        ds.put_dataframe(data)

    cfg["type"] = "sausage"
    with pytest.raises(TypeError, match="file type"):
        r.FileDataSink("bla", cfg)


# Test OracleDataSource and OracleDataSink


def test_get_user_pw(caplog):
    env = {"USR": "my_user", "PW": "my_pass"}
    conf = {
        "user_var": "USR",
        "password_var": "PW",
    }
    with mock.patch.dict(os.environ, env):
        user, pw = r.get_user_pw(conf["user_var"], conf["password_var"])
        assert user == env["USR"]
        assert pw == env["PW"]

    with mock.patch.dict(os.environ, {}):
        with pytest.raises(ValueError):
            r.get_user_pw(conf["user_var"], conf["password_var"])

    env2 = {"USR": "my_user"}
    with mock.patch.dict(os.environ, env2):
        user, pw = r.get_user_pw(conf["user_var"], conf["password_var"])
        assert user == env["USR"]
        assert pw is None
        assert "not set" in caplog.text.lower()


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


@mock.patch("{}.pd.read_sql".format(r.__name__))
@mock.patch("{}.get_user_pw".format(r.__name__), return_value=("foo", "bar"))
def test_oracledatasource_df(user_pw, pd_read, oracledatasource_cfg_and_data):
    """OracleDataSource should connect, read dataframe and return it unaltered."""
    cfg, dbms_cfg, data = oracledatasource_cfg_and_data()
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock
    pd_read.return_value = data

    ds = r.OracleDataSource("bla", cfg, dbms_cfg)
    df = ds.get_dataframe()

    pd.testing.assert_frame_equal(df, data)
    ora_mock.connect.assert_called_once()
    pd_read.assert_called_once()

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
@mock.patch("{}.pd.read_sql".format(r.__name__))
@mock.patch("{}.get_user_pw".format(r.__name__), return_value=("foo", "bar"))
def test_regression_oracle_nas_issue86(
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

    ds = r.OracleDataSource("bla", cfg, dbms_cfg)
    df = ds.get_dataframe()

    pd.testing.assert_frame_equal(df, expected)
    # assert df == expected
    ora_mock.connect.assert_called_once()
    pd_read.assert_called_once()

    del sys.modules["cx_Oracle"]


@mock.patch("{}.get_user_pw".format(r.__name__), return_value=("foo", "bar"))
def test_oracledatasource_notimplemented(
    user_pw, oracledatasource_cfg_and_data
):
    cfg, dbms_cfg, _ = oracledatasource_cfg_and_data()
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock

    ds = r.OracleDataSource("bla", cfg, dbms_cfg)
    with pytest.raises(NotImplementedError):
        ds.get_dataframe(buffer=True)
    with pytest.raises(NotImplementedError, match="get_dataframe"):
        ds.get_raw()

    del sys.modules["cx_Oracle"]


@mock.patch("{}.pd.DataFrame.to_sql".format(r.__name__))
@mock.patch("{}.get_user_pw".format(r.__name__), return_value=("foo", "bar"))
def test_oracledatasink_df(user_pw, df_write, oracledatasource_cfg_and_data):
    cfg, dbms_cfg, data = oracledatasource_cfg_and_data()
    del cfg["query"]
    cfg["table"] = "blabla"
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock
    df_write.return_value = data

    ds = r.OracleDataSink("bla", cfg, dbms_cfg)
    ds.put_dataframe(data)

    ora_mock.connect.assert_called_once()
    df_write.assert_called_once()

    del sys.modules["cx_Oracle"]


@mock.patch("{}.get_user_pw".format(r.__name__), return_value=("foo", "bar"))
def test_oracledatasink_notimplemented(user_pw, oracledatasource_cfg_and_data):
    cfg, dbms_cfg, data = oracledatasource_cfg_and_data()
    del cfg["query"]
    cfg["table"] = "blabla"
    ora_mock = mock.MagicMock()
    sys.modules["cx_Oracle"] = ora_mock

    ds = r.OracleDataSink("bla", cfg, dbms_cfg)
    with pytest.raises(NotImplementedError):
        ds.put_dataframe(data, buffer=True)
    with pytest.raises(NotImplementedError, match="put_dataframe"):
        ds.put_raw(data)

    del sys.modules["cx_Oracle"]


# Tests for to_plain_python_obj()
# fmt: off
ndarray_examples = [
    3,
    [1, 2, 3],
    [[1, 2], [3, 4]],
    [[[1, 2]], [[3, 4]]],
    [[.1, .2], [.3, .4]],
]
dataframe_examples = [
    (pd.DataFrame(), {}),
    (pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}),
        {'x': {0: 1, 1: 2, 2: 3}, 'y': {0: 4, 1: 5, 2: 6}})
]
mixed_examples = [
    ["a", 3, 3.7, [7], {"hello": 4, "something": ["else", "here", 12]}],
    [np.array(e) for e in ndarray_examples],
    {i: np.array(e) for i, e in enumerate(ndarray_examples)},
    ["a", 3, np.array([4, 5]), pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})],
]
# fmt: on


@pytest.mark.parametrize(
    "test_input,expected",
    zip([np.array(e) for e in ndarray_examples], ndarray_examples),
)
def test_to_plain_python_obj_numpy(test_input, expected):
    """Test to convert numpy arrays to json-compatible object."""
    output = r.to_plain_python_obj(test_input)
    assert output == expected
    # We should not get a json conversion error
    json.dumps(output)


@pytest.mark.parametrize("test_input,expected", dataframe_examples)
def test_to_plain_python_obj_pandas(test_input, expected):
    """Test to convert pandas arrays to json-compatible object."""
    output = r.to_plain_python_obj(test_input)
    assert output == expected
    # We should not get a json conversion error
    json.dumps(output)


@pytest.mark.parametrize("test_input", mixed_examples)
def test_to_plain_python_obj_mixed(test_input):
    """Test to convert mixed arrays to json-compatible object."""
    # It's enough that we don't get an exception here
    output = r.to_plain_python_obj(test_input)
    # We should not get a json conversion error
    json.dumps(output)


def test_to_plain_python_obj_error():
    """Test the error case."""

    class FailingObject:
        pass

    output = r.to_plain_python_obj(FailingObject())
    with pytest.raises(TypeError):
        json.dumps(output)


# Tests for order_columns


def test_order_columns_dict():
    d = {"c": [1, 2, 3], "b": [4, 5, 6], "a": [7, 8, 9]}
    expected = OrderedDict(a=[7, 8, 9], b=[4, 5, 6], c=[1, 2, 3])
    output = r.order_columns(d)
    assert output == expected
    assert list(output.keys()) == list(expected.keys())
    assert isinstance(output, type(expected))


def test_order_columns_df():
    df = pd.DataFrame(OrderedDict(c=[1, 2, 3], b=[4, 5, 6], a=[7, 8, 9]))
    expected = pd.DataFrame(OrderedDict(a=[7, 8, 9], b=[4, 5, 6], c=[1, 2, 3]))
    output = r.order_columns(df)
    pd.testing.assert_frame_equal(output, expected)


def test_order_columns_np():
    a = np.array(
        [(1, 4, 7), (2, 5, 8), (3, 6, 9)],
        dtype=[("c", "i4"), ("b", "i4"), ("a", "i4")],
    )
    expected = np.array(
        [(7, 4, 1), (8, 5, 2), (9, 6, 3)],
        dtype=[("a", "i4"), ("b", "i4"), ("c", "i4")],
    )

    # ordinary structured array
    output = r.order_columns(a)
    pd.testing.assert_frame_equal(pd.DataFrame(output), pd.DataFrame(expected))

    # record array
    a_r = np.rec.array(a)
    expected_r = np.rec.array(expected)
    output_r = r.order_columns(a_r)
    pd.testing.assert_frame_equal(
        pd.DataFrame(output_r), pd.DataFrame(expected_r)
    )


def test_order_columns_np_not_structured():
    a = np.array([(1, 4, 7), (2, 5, 8), (3, 6, 9)])
    with pytest.raises(TypeError):
        r.order_columns(a)


def test_order_columns_unsupported():
    with pytest.raises(TypeError):
        r.order_columns(["Hello", "there"])
