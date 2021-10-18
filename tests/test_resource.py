"""Tests for `mllaunchpad.resource` module."""

# Stdlib imports
import json
import logging
import os
from collections import OrderedDict
from random import random
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
        "api": {
            "name": "tree"
        }
    }
# fmt: on


@mock.patch("{}.os.path.exists".format(r.__name__), return_value=False)
@mock.patch("{}.os.makedirs".format(r.__name__))
def test_modelstore_create(makedirs, path_exists, modelstore_config):
    ms = r.ModelStore(modelstore_config)
    ms._ensure_location()
    makedirs.assert_called_once_with(
        modelstore_config["model_store"]["location"]
    )

    path_exists.reset_mock()
    makedirs.reset_mock()
    path_exists.return_value = True
    ms = r.ModelStore(modelstore_config)
    ms._ensure_location()
    assert not makedirs.called


@mock.patch("{}.os.path.exists".format(r.__name__), return_value=False)
@mock.patch("{}.os.makedirs".format(r.__name__))
@mock.patch("{}.shutil.copy".format(r.__name__))
@mock.patch(
    "{}.glob.glob".format(r.__name__), return_value=["old.pkl", "old.json"]
)
def test_modelstore_dump(glob, copy, makedirs, path_exists, modelstore_config):
    with mock.patch(
        "{}.open".format(r.__name__), mock.mock_open(), create=True
    ) as mo:
        ms = r.ModelStore(modelstore_config)
        ms.dump_trained_model(
            modelstore_config, {"pseudo_model": 1}, {"pseudo_metrics": 2}
        )

    model_conf = modelstore_config["model"]
    base_name = os.path.join(
        modelstore_config["model_store"]["location"],
        "{}_{}".format(model_conf["name"], model_conf["version"]),
    )
    calls = [
        mock.call("{}.pkl".format(base_name), "wb"),
        mock.call("{}.json".format(base_name), "w", encoding="utf-8"),
    ]
    mo.assert_has_calls(calls, any_order=True)


@mock.patch("{}.os.path.exists".format(r.__name__), return_value=True)
@mock.patch("{}.pickle.dump".format(r.__name__))
@mock.patch("{}.json.dump".format(r.__name__))
def test_modelstore_dump_extra_model_keys(
    jsond, pickled, path_exists, modelstore_config
):
    modelstore_config["model"]["extraparam"] = 42
    modelstore_config["model"]["anotherparam"] = 23
    modelstore_config["model"]["created"] = "colliding keys should not occur"
    with mock.patch(
        "{}.open".format(r.__name__), mock.mock_open(), create=True
    ) as _:
        ms = r.ModelStore(modelstore_config)
        ms.dump_trained_model(
            modelstore_config, {"pseudo_model": 1}, {"pseudo_metrics": 2}
        )

    dumped = jsond.call_args[0][0]
    print(modelstore_config)
    print(dumped)
    assert "extraparam" in dumped
    assert dumped["extraparam"] == 42
    assert "anotherparam" in dumped
    assert dumped["anotherparam"] == 23
    assert dumped["created"] != "colliding keys should not occur"


@mock.patch("{}.os.path.exists".format(r.__name__), return_value=True)
@mock.patch("{}.pickle.dump".format(r.__name__))
@mock.patch("{}.json.dump".format(r.__name__))
def test_modelstore_train_report(
    jsond, pickled, path_exists, modelstore_config
):
    with mock.patch(
        "{}.open".format(r.__name__), mock.mock_open(), create=True
    ) as _:
        ms = r.ModelStore(modelstore_config)
        ms.add_to_train_report("report_key", "report_val")
        ms.dump_trained_model(
            modelstore_config, {"pseudo_model": 1}, {"pseudo_metrics": 2}
        )

    dumped = jsond.call_args[0][0]
    print(modelstore_config)
    print(dumped)
    assert "train_report" in dumped
    assert "report_key" in dumped["train_report"]
    assert dumped["train_report"]["report_key"] == "report_val"

    assert "system" in dumped
    assert "mllaunchpad_version" in dumped["system"]
    assert "platform" in dumped["system"]
    assert "packages" in dumped["system"]


@mock.patch("{}.os.path.exists".format(r.__name__), return_value=True)
@mock.patch(
    "{}.ModelStore._load_metadata".format(r.__name__),
    side_effect=lambda _: {"the_json": round(random() * 1000)},
)
def test_list_models(_load_metadata, path_exists, modelstore_config, caplog):
    model_jsons = [
        "mymodel_1.0.0.json",
        "mymodel_1.1.0.json",
        "anothermodel_0.0.1.json",
    ]
    backup_jsons = [
        "mymodel_1.0.0_2021-08-01_18-00-00.json",
        "mymodel_1.0.0_2021-07-31_12-00-00",
    ]

    def my_glob(pattern):
        if "previous" in pattern.lower():
            return backup_jsons
        else:
            return model_jsons

    with mock.patch(
        "{}.glob.glob".format(r.__name__), side_effect=my_glob,
    ):
        with caplog.at_level(logging.DEBUG):
            ms = r.ModelStore(modelstore_config)
            models = ms.list_models()

    print(models)
    assert (
        len(models) == 2
    )  # one model ID named "mymodel" and one named "anothermodel"
    assert models["mymodel"]["latest"] == models["mymodel"]["1.1.0"]
    assert len(models["mymodel"]["backups"]) == 2
    assert models["anothermodel"]["backups"] == []
    assert "ignoring" not in caplog.text.lower()


@mock.patch("{}.os.path.exists".format(r.__name__), return_value=True)
@mock.patch(
    "{}.ModelStore._load_metadata".format(r.__name__),
    side_effect=lambda _: {"the_json": round(random() * 1000)},
)
def test_list_models_ignore_obsolete_backups(
    _load_metadata, path_exists, modelstore_config, caplog
):
    model_jsons = [
        "mymodel_1.0.0.json",
        "mymodel_1.1.0.json",
        "anothermodel_0.0.1.json",
    ]
    backup_jsons = [
        "mymodel_1.0.0_2021-08-01_18-00-00.json",
        "OBSOLETE-IGNORED_1.0.0_2021-07-31_12-00-00",
    ]

    def my_glob(pattern):
        if "previous" in pattern.lower():
            return backup_jsons
        else:
            return model_jsons

    with mock.patch(
        "{}.glob.glob".format(r.__name__), side_effect=my_glob,
    ):
        with caplog.at_level(logging.DEBUG):
            ms = r.ModelStore(modelstore_config)
            models = ms.list_models()

    print(models)
    assert "ignoring" in caplog.text.lower()


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
        mock.call("{}.json".format(base_name), "r", encoding="utf-8"),
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


def test___get_all_classes():
    """Retrieve a type which subclasses the given type"""
    config = {"plugins": ["tests.mock_plugin"]}
    classes = r._get_all_classes(config, r.DataSource)
    assert "food" in classes
    classes = r._get_all_classes(config, r.DataSink)
    assert "food" in classes


def test_create_data_sources_and_sinks():
    conf = {
        "plugins": ["tests.mock_plugin"],
        "datasources": {
            "bla": {"type": "food", "path": "some/path", "tags": "train"},
        },
        "datasinks": {
            "foo": {"type": "food", "path": "some/path"},
            "blargh": {
                "type": "food",
                "path": "some/path",
                "tags": "weirdtag",
            },
        },
    }
    src, snk = r.create_data_sources_and_sinks(conf, tags=["weirdtag"])
    assert "bla" not in src
    assert "foo" in snk
    assert "blargh" in snk
    src, snk = r.create_data_sources_and_sinks(conf)
    assert "bla" in src
    assert "foo" in snk
    assert "blargh" in snk
    with pytest.raises(ValueError, match="available"):
        conf["datasources"]["bla"]["type"] = "will_not_be_found"
        r.create_data_sources_and_sinks(conf)


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

    def get_dataframe(self, params=None, chunksize=None):
        df = pd.DataFrame(params)
        return df

    def get_raw(self, params=None, chunksize=False):
        raw = params
        return raw


@pytest.mark.parametrize(
    "expires, expected_cached", [(0, False), (100000, True), (-1, True)]
)
def test_datasource_expires_df(
    expires, expected_cached, datasource_expires_config
):
    args = {"a": [1, 2, 3], "b": [3, 4, 5]}
    ds = MockDataSource("mock", datasource_expires_config(expires))

    # 1st DF read
    df1 = ds.get_dataframe(params=args.copy())
    pd.testing.assert_frame_equal(df1, pd.DataFrame(args))
    assert df1 is not pd.DataFrame(args)

    # 2nd DF read
    df2 = ds.get_dataframe(params=args.copy())
    pd.testing.assert_frame_equal(df2, pd.DataFrame(args))
    assert (df2 is df1) == expected_cached

    # 3rd DF read
    df3 = ds.get_dataframe(params=args.copy())
    pd.testing.assert_frame_equal(df3, pd.DataFrame(args))
    assert (df3 is df1) == expected_cached


def test_datasource_expires_chunksize_error(datasource_expires_config):
    """chunksize must not be used with expires != 0"""
    ds1 = MockDataSource("mock", datasource_expires_config(-1))
    with pytest.raises(ValueError, match="incompatible"):
        _ = ds1.get_dataframe(chunksize=5)
    ds2 = MockDataSource("mock", datasource_expires_config(20000))
    with pytest.raises(ValueError, match="incompatible"):
        _ = ds2.get_dataframe(chunksize=5)
    ds3 = MockDataSource("mock", datasource_expires_config(0))
    _ = ds3.get_dataframe(chunksize=5)
    ds4 = MockDataSource("mock", datasource_expires_config(20000))
    _ = ds4.get_dataframe()


@pytest.mark.parametrize(
    "expires, expected_cached", [(0, False), (100000, True), (-1, True)]
)
def test_datasource_expires_raw(
    expires, expected_cached, datasource_expires_config
):
    args = {"a": [1, 2, 3], "b": [3, 4, 5]}
    ds = MockDataSource("mock", datasource_expires_config(expires))

    # 1st raw read
    raw1 = ds.get_raw(params=args.copy())
    assert raw1 == args

    # 2nd raw read
    raw2 = ds.get_raw(params=args.copy())
    assert raw2 == args
    assert (raw2 is raw1) == expected_cached


def test_datasource_memoization_df(datasource_expires_config):
    args1 = {"a": [1, 2, 3], "b": [3, 4, 5]}
    args2_same = {"a": [1, 2, 3], "b": [3, 4, 5]}
    args3_different = {"A": [3, 2, 1], "B": [3, 4, 5]}
    args4_again_different = {"C": [3, 2, 1], "D": [3, 4, 5]}
    cfg = datasource_expires_config(-1)  # use cache
    cfg["cache_size"] = 2
    ds = MockDataSource("mock", cfg)

    # 1st DF read (cached as 1st cache element)
    df1 = ds.get_dataframe(params=args1.copy())
    pd.testing.assert_frame_equal(df1, pd.DataFrame(args1))
    assert df1 is not pd.DataFrame(args1)  # not from cache

    # 2nd DF read (getting from cache)
    df2 = ds.get_dataframe(params=args2_same.copy())
    pd.testing.assert_frame_equal(df2, pd.DataFrame(args2_same))
    assert df2 is df1  # from cache

    # 3rd DF read (different params passed, will be cached as 2nd cache element)
    df3 = ds.get_dataframe(params=args3_different.copy())
    pd.testing.assert_frame_equal(df3, pd.DataFrame(args3_different))
    assert df3 is not df2  # not from cache
    assert df3 is not df1  # not from cache

    # 4rth DF read (original params passed again -- it is still in the cache due to size of 2)
    df4 = ds.get_dataframe(params=args1.copy())
    pd.testing.assert_frame_equal(df4, pd.DataFrame(args1))
    assert df4 is df1  # from cache

    # 5th DF read (yet unseen params passed -- will be cached, replacing args1)
    df5 = ds.get_dataframe(params=args4_again_different.copy())
    pd.testing.assert_frame_equal(df5, pd.DataFrame(args4_again_different))
    assert df5 is not df4  # not from cache
    assert df5 is not df3  # not from cache
    assert df5 is not df2  # not from cache
    assert df5 is not df1  # not from cache

    # 6th DF read (original params passed -- not in cache any more due to cache size limit of 2)
    df6 = ds.get_dataframe(params=args1.copy())
    pd.testing.assert_frame_equal(df6, pd.DataFrame(args1))
    assert df6 is not df5  # not from cache
    assert df6 is not df4  # not from cache
    assert df6 is not df3  # not from cache
    assert df6 is not df2  # not from cache
    assert df6 is not df1  # not from cache


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
