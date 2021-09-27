"""Convenience functions for executing training, testing and prediction"""

# Stdlib imports
import logging
import sys
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

# Project imports
from mllaunchpad import resource
from mllaunchpad.model_interface import ModelInterface, ModelMakerInterface


logger = logging.getLogger(__name__)


_cached_model_stores: Dict = {}
_cached_model_tuples: Dict = {}
_cached_data_source_sink_tuples: Dict = {}
_cached_model_makers: Dict = {}
_cached_model_classes: Dict = {}
_current_train_report: Optional[Dict[str, Any]] = None

suppress_order_columns_not_used_warning = (
    "To adjust this warning, set model config's `order_columns_not_used_warning` "
    "to `always` (default), `test_and_predict` or `never`."
)


def train_model(
    complete_conf: Dict,
    cache: bool = True,
    persist: bool = True,
    test: bool = True,
    model: Optional[ModelInterface] = None,
):
    """Train and test a model as specified in the configuration and persist
    it in the model store.

    :param complete_conf: configuration dict
    :type complete_conf: dict
    :param cache: Whether to cache the data sources/sinks and helper objects (cache lookup is done by model name and model version). If in doubt, leave at default.
    :type cache: optional bool, default: True
    :param persist: Whether to store the trained model in the location configured by `model_cache:`. This parameter exists mainly for making debugging and unit testing your model's code easier.
    :type persist: optional bool, default: True
    :param test: Whether to test the model after training. This parameter exists mainly for making debugging and unit testing your model's code easier.
    :type test: optional bool, default: True
    :param model: Use this model as previous model instead trying to load it from `model_store`. This parameter exists mainly for making debugging and unit testing your model's code easier.
    :type model: optional object implementing ModelInterface, default: None

    :return: Tuple of (object implementing ModelInterface, metrics)
    """
    # if persist and not test:
    #     raise ValueError("If you set `test` to False, you have to set `persist` to False, too. "
    #                      "A model cannot be persisted without any test metrics")

    logger.debug("Creating trained model...")
    user_mm = _get_model_maker(complete_conf, cache=cache)

    model_conf = complete_conf["model"]

    if model:
        old_inner_model = model.contents
    else:
        try:
            logger.debug("Trying to load old model...")
            old_model_wrapper, _ = _get_model(complete_conf, cache=cache)
            old_inner_model = old_model_wrapper.contents
        except FileNotFoundError:
            logger.info("No old model to load")
            old_inner_model = None
        except AttributeError as e:
            if "module '{}'".format(model_conf["module"]) in str(e):
                logger.info(
                    "No model loaded. Model class appears to have been renamed since last training"
                )
                old_inner_model = None
            else:
                raise e

    dso_train, dsi_train = _get_data_sources_and_sinks(
        complete_conf, tags=["train"], cache=cache
    )

    report_dict: Dict[str, Any]
    with train_report() as report_dict:
        inner_model = user_mm.create_trained_model(
            model_conf, dso_train, dsi_train, old_model=old_inner_model
        )
        m_cls = _get_model_class(complete_conf, cache=cache)
        model_wrapper: ModelInterface = m_cls(contents=inner_model)

        if resource._order_columns_called:
            model_wrapper.have_columns_been_ordered = True
        elif (
            "order_columns_not_used_warning" not in model_conf
            or model_conf["order_columns_not_used_warning"] == "always"
        ):
            logger.warning(
                "Training code does not call function order_columns. "
                + suppress_order_columns_not_used_warning
            )

        if not isinstance(model_wrapper, ModelInterface):
            logger.warning(
                "Model's class is not a subclass of ModelInterface: %s",
                model_wrapper,
            )

        metrics = {}
        if test:
            logger.debug("Testing trained model...")
            dso_test, dsi_test = _get_data_sources_and_sinks(
                complete_conf, tags=["test"], cache=cache
            )
            metrics = user_mm.test_trained_model(
                model_conf, dso_test, dsi_test, inner_model
            )
            _check_ordered_columns(
                complete_conf, model_wrapper, "testing code", times=2
            )

        if persist:
            model_store = _get_model_store(complete_conf, cache=cache)
            for name, val in report_dict.items():
                model_store.add_to_train_report(name, val)
            model_store.add_to_train_report("algorithm", repr(inner_model))
            model_store.dump_trained_model(
                complete_conf, model_wrapper, metrics
            )

    logger.info(
        "Created%s trained model %s, version %s, metrics %s",
        " and stored" if persist else "",
        model_conf["name"],
        model_conf["version"],
        metrics,
    )

    return model_wrapper, metrics


def retest(
    complete_conf: Dict,
    cache: bool = True,
    persist: bool = True,
    model: Optional[ModelInterface] = None,
):
    """Retest a model as specified in the configuration and persist its
    test metrics in the model store.

    :param complete_conf: configuration dict
    :type complete_conf: dict
    :param cache: Whether to cache the data sources/sinks and helper objects (cache lookup is done by model name and model version). If in doubt, leave at default.
    :type cache: optional bool, default: True
    :param persist: Whether to update the model in `model_cache:` with the test metrics. This parameter exists mainly for making debugging and unit testing your model's code easier.
    :type persist: optional bool, default: True
    :param model: Test this model instead of loading it from `model_store`. This parameter exists mainly for making debugging and unit testing your model's code easier.
    :type model: optional object implementing ModelInterface, default: None

    :return: test_metrics
    """
    logger.debug("Retesting existing trained model...")
    dso, dsi = _get_data_sources_and_sinks(
        complete_conf, tags=["test"], cache=cache
    )
    user_mm = _get_model_maker(complete_conf, cache=cache)
    model_conf = complete_conf["model"]

    if model:
        model_wrapper = model
    else:
        model_wrapper, _ = _get_model(complete_conf, cache=cache)

    inner_model = model_wrapper.contents

    test_metrics = user_mm.test_trained_model(
        model_conf, dso, dsi, inner_model
    )
    _check_ordered_columns(complete_conf, model_wrapper, "retesting code")

    if persist:
        model_store = _get_model_store(complete_conf, cache=cache)
        model_store.update_model_metrics(model_conf, test_metrics)

    logger.info(
        "Retested existing model %s, version %s, new metrics %s",
        model_conf["name"],
        model_conf["version"],
        test_metrics,
    )

    return test_metrics


def predict(
    complete_conf: Dict,
    arg_dict: Optional[Dict] = None,
    cache: bool = True,
    model: Optional[ModelInterface] = None,
    use_live_code: bool = False,
):
    """Carry out prediction for the model specified in the configuration.

    :param complete_conf: configuration dict
    :type complete_conf: dict
    :param cache: Whether to cache the data sources/sinks and helper objects (cache lookup is done by model name and model version). If in doubt, leave at default.
    :type cache: optional bool, default: True
    :param arg_dict: Arguments dict for the prediction (analogous to what it would get from a web API)
    :type arg_dict: optional Dict, default: None
    :param model: Test this model instead of loading it from `model_store`. This parameter exists mainly for making debugging and unit testing your model's code easier.
    :type model: optional object implementing ModelInterface, default: None
    :param use_live_code: Use the current `predict` function instead of the one persisted with the model in the `model_store`. This parameter exists mainly for making debugging and unit testing your model's code easier.
    :type use_live_code: optional bool, default: False

    :return: model's prediction output
    """
    logger.debug("Applying model for prediction...")

    dso, dsi = _get_data_sources_and_sinks(
        complete_conf, tags=["predict"], cache=cache
    )
    model_conf = complete_conf["model"]

    if model:
        model_wrapper = model
    else:
        model_wrapper, _ = _get_model(complete_conf, cache=cache)

    inner_model = model_wrapper.contents

    if use_live_code:
        # Create a fresh model object from current code and transplant existing contents
        m_cls = _get_model_class(complete_conf, cache=cache)
        curr_model_wrapper: ModelInterface = m_cls(contents=inner_model)
        model_wrapper = curr_model_wrapper

    output = model_wrapper.predict(
        model_conf, dso, dsi, inner_model, arg_dict or {}
    )
    _check_ordered_columns(complete_conf, model_wrapper, "prediction code")

    output = resource.to_plain_python_obj(output)

    return output


def clear_caches():
    global _cached_model_stores
    global _cached_model_tuples
    global _cached_data_source_sink_tuples
    global _cached_model_makers
    global _cached_model_classes

    _cached_model_stores.clear()
    _cached_model_tuples.clear()
    _cached_data_source_sink_tuples.clear()
    _cached_model_makers.clear()
    _cached_model_classes.clear()


def _model_key(model_conf):
    return model_conf["name"] + "_" + model_conf["version"]


def _find_subclass(module_name, superclass):
    """Locate and instantiate class of data-scientist-provided ModelMaker
    or model class.
    For this to work, your model module (.py file) needs to be in python's
    sys.path (usually the case).
    Also set the config's model: module property accordingly.

    Params:
        module_name: the name of the module
        superclass: subclasses of which class to locate

    Returns:
        subclass as found in data scientist's module
    """

    if "." not in sys.path:
        sys.path.append(".")

    __import__(module_name)

    classes = superclass.__subclasses__()
    if len(classes) != 1:
        raise ValueError(
            "The configured model module (.py file) must contain "
            + "one {}-inheriting class definition, but contains {}.".format(
                superclass, len(classes)
            )
        )

    cls = classes[0]
    logger.debug("Found %s class named %s", superclass, cls)

    return cls


def _get_model_maker(complete_conf, cache=True):
    """Locate and instantiate class of data-scientist-provided ModelMaker
    (which the data scientist inherited from ModelMakerInterface).
    For this to work, your model module (.py file) needs to be in python's
    sys.path (usually the case).
    Also set the config's model: module property accordingly.

    Params:
        complete_conf: the configuration dict

    Returns:
        instance of data scientist's ModelMaker model factory object
    """
    global _cached_model_makers

    key = _model_key(complete_conf["model"])

    mm = _cached_model_makers.get(key)
    if mm is None:
        logger.debug("Locating and instantiating ModelMaker...")
        mm_cls = _find_subclass(
            complete_conf["model"]["module"], ModelMakerInterface
        )
        mm = mm_cls()
        if cache:
            _cached_model_makers[key] = mm
        logger.debug("Instantiated ModelMaker object %s", mm)

    return mm


def _get_model_class(complete_conf, cache=True):
    """Locate class of data-scientist-provided model
    (which the data scientist inherited from ModelInterface).
    For this to work, your model module (.py file) needs to be in python's
    sys.path (usually the case).
    Also set the config's model: module property accordingly.

    Params:
        complete_conf: the configuration dict

    Returns:
        data scientist's Model class
    """
    global _cached_model_classes

    key = _model_key(complete_conf["model"])

    m_cls = _cached_model_classes.get(key)
    if m_cls is None:
        logger.debug("Locating Model class...")
        m_cls = _find_subclass(
            complete_conf["model"]["module"], ModelInterface
        )
        if cache:
            _cached_model_classes[key] = m_cls

    return m_cls


def _get_model_store(complete_conf, cache=True):
    global _cached_model_stores

    key = _model_key(complete_conf["model"])

    model_store = _cached_model_stores.get(key) or resource.ModelStore(
        complete_conf
    )

    if cache:
        _cached_model_stores[key] = model_store

    return model_store


def _get_model(complete_conf, cache=True):
    global _cached_model_tuples
    model_store = _get_model_store(complete_conf, cache=cache)

    model_conf = complete_conf["model"]
    key = _model_key(model_conf)

    model_tuple = _cached_model_tuples.get(key)
    if model_tuple is None:
        logger.info("Loading model...")
        model_wrapper, meta = model_store.load_trained_model(model_conf)
        logger.info(
            "Model loaded: {}, version: {}, created {}".format(
                meta["name"], meta["version"], meta["created"]
            )
        )

        model_tuple = (model_wrapper, meta)

        if cache:
            _cached_model_tuples[key] = model_tuple

    return model_tuple


def _get_data_sources_and_sinks(complete_conf, tags=None, cache=True):
    global _cached_data_source_sink_tuples

    key = _model_key(complete_conf["model"]) + str(tags)

    ds_tuple = _cached_data_source_sink_tuples.get(key)
    if ds_tuple is None:
        logger.info("Initializing datasources...")
        dso, dsi = resource.create_data_sources_and_sinks(
            complete_conf, tags=tags
        )
        logger.info(
            "%s datasource(s) initialized: %s", len(dso), list(dso.keys())
        )
        logger.info(
            "%s datasink(s) initialized: %s", len(dsi), list(dsi.keys())
        )

        ds_tuple = (dso, dsi)

        if cache:
            _cached_data_source_sink_tuples[key] = ds_tuple

    return ds_tuple


def _check_ordered_columns(complete_conf, model_wrapper, what: str, times=1):
    if (
        "order_columns_not_used_warning" in complete_conf["model"]
        and str(
            complete_conf["model"]["order_columns_not_used_warning"]
        ).lower()
        == "never"
    ):
        return
    if model_wrapper.have_columns_been_ordered:
        if resource._order_columns_called < times:
            logger.warning(
                "Model has been trained on ordered columns, but "
                "{} does not call function order_columns. {}".format(
                    what, suppress_order_columns_not_used_warning
                )
            )


@contextmanager
def train_report() -> Iterator[Dict[str, Any]]:
    # initialize
    global _current_train_report
    if _current_train_report is not None:
        raise RuntimeError(
            "Cannot initialize a train_report context within another train_report context."
        )
    _current_train_report = {}
    try:
        yield _current_train_report
    finally:
        # release
        _current_train_report = None


def _add_to_train_report(name: str, value) -> None:
    """Add a piece of information to the train report during training.

    The train report is part of the model's metadata that is saved to the model store.
    Use :func:`mllaunchpad.list_models` to query metadata from the model store.

    This function is supposed to be called from your :func:`~mllaunchpad.ModelMakerInterface.create_trained_model` or
    :func:`~mllaunchpad.ModelMakerInterface.test_trained_model` implementation. You can pass any values that are
    JSON-able, same as with :func:`~mllaunchpad.ModelMakerInterface.test_trained_model`'s
    returned metrics.

    However, if the value is a DataFrame, it will be summarized (using `pd.describe()`). You can use this for example
    to improve traceability of your trained models and for some basic sanity checks of training data distribution.

    :param name: Key to save the information under (e.g. "meaning_of_life")
    :type name: str
    :param value: Value to save. Any JSON-able value or structure will work. Pandas DataFrames will be summarized instead of saved.
    :type value: str, number, list, dict, Numpy Array or Pandas DataFrame
    """
    global _current_train_report
    if _current_train_report is None:
        logger.info(
            'Ignoring attempt to add record "{}" to train report '
            "(hint: 'mllaunchpad.report()' does nothing when re-testing).".format(
                name
            )
        )
    else:
        import pandas as pd

        if isinstance(value, pd.DataFrame):
            data_dict = _current_train_report.get("data", {})
            data_dict[name] = {
                "nrows": value.shape[0],
                "ncols": value.shape[1],
                "colnames": list(value.columns),
                "dtypes": [str(dt) for dt in value.dtypes],
                "description": value.describe(),
            }
            logger.info(
                "Train report data: {}={}".format(name, data_dict[name])
            )
            _current_train_report["data"] = data_dict
        else:
            logger.info("Train report: {}={}".format(name, value))
            _current_train_report[name] = value
