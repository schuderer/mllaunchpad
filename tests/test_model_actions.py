"""Tests for `mllaunchpad.model_actions` module."""

# Stdlib imports
import logging
from unittest import mock

# Third-party imports
import pytest

# Project imports
from mllaunchpad import model_actions as ma

from .mock_model import MockModelClass, MockModelMakerClass


@pytest.fixture()
def config():
    return {
        "model_store": {"location": "asdfasdf"},
        "model": {"name": "foo", "version": "1.0.0", "module": "blamodule"},
    }


#
# @pytest.fixture()
# def model_class():
#     from mllaunchpad import ModelInterface
#     ma.clear_caches()
#
#     class MockModelClass(ModelInterface):
#         def predict(self, model_conf, data_sources, data_sinks, model, args_dict):
#             return None
#
#     yield MockModelClass
#
#     del MockModelClass
#     ma.clear_caches()
#     import gc
#     gc.collect()
#
#
# @pytest.fixture()
# def model_maker():
#     from mllaunchpad import ModelMakerInterface
#
#     class MockModelMakerClass(ModelMakerInterface):
#         def create_trained_model(self, model_conf, data_sources, data_sinks, old_model=None):
#             return None
#
#         def test_trained_model(self, model_conf, data_sources, data_sinks, model):
#             return None
#
#     yield MockModelMakerClass
#
#     del MockModelMakerClass
#     import gc
#     gc.collect()
#
#     # Hacky, but somehow del leaves subclasses around in some situations
#     for sub_that_should_not_exist in ModelMakerInterface.__subclasses__():
#         sub_that_should_not_exist.__bases__ = (type("OtherClass", (object,), {}),)


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_train_model(gm, ms, imp, config):
    ma.train_model(config, cache=False)
    ms_instance = ms.return_value
    ms_instance.dump_trained_model.assert_called_once()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_train_model_no_test(gm, ms, imp, config, caplog):
    with caplog.at_level(logging.DEBUG):
        _, metrics = ma.train_model(config, cache=False, test=False)
    assert metrics == {}
    assert "training".lower() in caplog.text.lower()
    ms_instance = ms.return_value
    ms_instance.dump_trained_model.assert_called_once()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_train_model_no_persist(gm, ms, imp, config):
    model, _ = ma.train_model(config, cache=False, persist=False)
    ms_instance = ms.return_value
    ms_instance.dump_trained_model.assert_not_called()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_train_model_own_model(gm, ms, imp, config):
    model, _ = ma.train_model(config, cache=False, model=mock.Mock())
    gm.assert_not_called()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    side_effect=FileNotFoundError("blabla"),
)
def test_train_model_not_found(gm, ms, imp, config, caplog):
    with caplog.at_level(logging.DEBUG):
        ma.train_model(config, cache=False)
    assert "No old model".lower() in caplog.text.lower()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    side_effect=AttributeError(
        r"AttributeError: Can't get attribute 'MyExampleModel' on <module 'blamodule' from '.\\tree_model.py'>"
    ),
)
def test_train_model_renamed(gm, ms, imp, config, caplog):
    with caplog.at_level(logging.DEBUG):
        ma.train_model(config, cache=False)
    assert "renamed".lower() in caplog.text.lower()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_retest(gm, ms, imp, config):
    ma.retest(config, cache=False)
    gm.assert_called_once()
    ms_instance = ms.return_value
    ms_instance.update_model_metrics.assert_called_once()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_retest_own_model(gm, ms, imp, config):
    ma.retest(config, cache=False, model=mock.Mock())
    gm.assert_not_called()
    ms_instance = ms.return_value
    ms_instance.update_model_metrics.assert_called_once()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_retest_no_persist(gm, ms, imp, config):
    ma.retest(config, cache=False, persist=False)
    gm.assert_called_once()
    ms_instance = ms.return_value
    ms_instance.update_model_metrics.assert_not_called()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_predict(gm, ms, imp, config):
    ma.predict(config, cache=False)
    gm.assert_called_once()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_predict_own_model(gm, ms, imp, config):
    mock_model_wrapper = mock.Mock()
    mock_model_wrapper.predict.return_value = "blafoo"
    result = ma.predict(config, cache=False, model=mock_model_wrapper)
    mock_model_wrapper.predict.assert_called_once()
    assert result == "blafoo"
    gm.assert_not_called()


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
@mock.patch(
    "{}._get_model".format(ma.__name__),
    autospec=True,
    return_value=(mock.Mock(), mock.MagicMock()),
)
def test_predict_live_code(gm, ms, imp, config):
    ma.predict(config, cache=False, use_live_code=True)
    gm.return_value[0].predict.assert_not_called()


def test_clear_caches():
    # TODO: This is testing the implementation, should test the functionality instead
    ma._cached_model_stores = {"a": 1}
    ma._cached_model_tuples = {"a": 1}
    ma._cached_data_source_sink_tuples = {"a": 1}
    ma._cached_model_makers = {"a": 1}
    ma._cached_model_classes = {"a": 1}

    ma.clear_caches()

    assert ma._cached_model_stores == {}
    assert ma._cached_model_tuples == {}
    assert ma._cached_data_source_sink_tuples == {}
    assert ma._cached_model_makers == {}
    assert ma._cached_model_classes == {}


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
def test__get_model_maker(ms_class, imp, config):
    ma.clear_caches()
    mm = ma._get_model_maker(config)
    imp.assert_called_with("blamodule")
    assert isinstance(mm, MockModelMakerClass)


@mock.patch("builtins.__import__")
@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
def test__get_model_class(ms_class, imp, config):
    ma.clear_caches()
    mc = ma._get_model_class(config)
    imp.assert_called_with("blamodule")
    assert mc is MockModelClass


# @mock.patch("builtins.__import__")
# @mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
# def test__get_model_class_error(ms_class, imp, config):
#     ma.clear_caches()
#
#     from mllaunchpad import ModelInterface
#     class AClassTooMany(ModelInterface):
#         pass
#
#     with pytest.raises(ValueError, match="class definition"):
#         ma._get_model_class(config)
#
#     del AClassTooMany


@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
def test__get_model_store(ms_class, config):
    ms = mock.Mock()
    ms_class.return_value = ms
    ma.clear_caches()

    ms1 = ma._get_model_store(config)
    assert ms1 is ms


@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
def test__get_model_store_caching(ms_class, config):
    # caching
    ma.clear_caches()
    ms_class.return_value = 1
    ms1 = ma._get_model_store(config)
    ms_class.return_value = 2
    ms2 = ma._get_model_store(config)
    assert ms1 is ms2
    assert ms2 == 1

    # no caching
    ma.clear_caches()
    ms_class.return_value = 1
    ms1 = ma._get_model_store(config, cache=False)
    ms_class.return_value = 2
    ms2 = ma._get_model_store(config)
    assert ms1 is not ms2


@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
def test__get_model(ms_class, config):
    ma.clear_caches()
    model_wrapper = mock.Mock()
    model_meta = mock.MagicMock()
    ms_class.return_value.load_trained_model.return_value = (
        model_wrapper,
        model_meta,
    )

    mw, mm = ma._get_model(config)
    assert mw is model_wrapper
    assert mm is model_meta


@mock.patch("{}.resource.ModelStore".format(ma.__name__), autospec=True)
def test__get_model_caching(ms_class, config):
    # caching
    ma.clear_caches()
    ms_class.return_value.load_trained_model.return_value = (
        mock.Mock(),
        mock.MagicMock(),
    )

    mw1, mm1 = ma._get_model(config)
    ms_class.return_value.load_trained_model.return_value = (
        mock.Mock(),
        mock.MagicMock(),
    )
    mw2, mm2 = ma._get_model(config)
    assert mw1 is mw2
    assert mm1 is mm2

    # no caching
    ma.clear_caches()
    ms_class.return_value.load_trained_model.return_value = (
        mock.Mock(),
        mock.MagicMock(),
    )

    mw1, mm1 = ma._get_model(config, cache=False)
    ms_class.return_value.load_trained_model.return_value = (
        mock.Mock(),
        mock.MagicMock(),
    )
    mw2, mm2 = ma._get_model(config)
    assert mw1 is not mw2
    assert mm1 is not mm2


def test__check_ordered_columns(caplog):
    from mllaunchpad.resource import order_columns

    with caplog.at_level(logging.INFO):
        dummy_config = {"model": {}}
        mock_wrapper = MockModelClass()

        ma._check_ordered_columns(dummy_config, mock_wrapper, "never_ordered")
        assert "never_ordered".lower() not in caplog.text.lower()

        mock_wrapper.have_columns_been_ordered = True
        ma._check_ordered_columns(
            dummy_config, mock_wrapper, "ordered_only_in_train"
        )
        assert (
            "ordered_only_in_train does not call".lower()
            in caplog.text.lower()
        )

        order_columns({"a": 1})
        ma._check_ordered_columns(
            dummy_config, mock_wrapper, "ordered_in_train_and_now"
        )
        assert "ordered_in_train_and_now".lower() not in caplog.text.lower()


def test_train_report_context(caplog):
    with caplog.at_level(logging.INFO):
        with ma.train_report() as tr:
            ma._add_to_train_report("myname", "myvalue")
            assert ma._current_train_report is tr

        assert tr["myname"] == "myvalue"
        assert "{}={}".format("myname", "myvalue") in caplog.text


def test_train_report_uninitialized(caplog):
    with caplog.at_level(logging.INFO):
        ma._add_to_train_report("myname", "myvalue")
        assert "Ignoring" in caplog.text

        with ma.train_report():
            pass

        ma._add_to_train_report("myname", "myvalue")
        assert "{}={}".format("myname", "myvalue") not in caplog.text


def test_train_report_reentrant():
    with ma.train_report():
        with pytest.raises(RuntimeError):
            with ma.train_report():
                pass
