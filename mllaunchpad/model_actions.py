# -*- coding: utf-8 -*-

"""Convenience functions for executing training, testing and prediction"""

# Stdlib imports
import logging
import sys

# Application imports
from mllaunchpad import resource
from mllaunchpad.model_interface import ModelInterface, ModelMakerInterface

logger = logging.getLogger(__name__)


_cached_model_stores = {}
_cached_model_tuples = {}
_cached_data_source_sink_tuples = {}
_cached_model_makers = {}
_cached_model_classes = {}


def train_model(complete_conf, cache=True):
    """Train and test a model as specified in the configuration and persist
    it in the model store

    Params:
        complete_conf: configuration dict
        cache:         (default: True) whether to cache the data sources/sinks and helper objects (cache lookup is done by model name and model version). If in doubt, leave at default.

    Returns:
        (model, metrics) tuple
    """
    logger.debug("Creating trained model...")
    user_mm = _get_model_maker(complete_conf, cache=cache)

    dso, dsi = _get_data_sources_and_sinks(
        complete_conf, tags=["train", "test"], cache=cache
    )

    model_conf = complete_conf["model"]

    try:
        logger.debug("Trying to load old model...")
        old_model_wrapper, meta = _get_model(complete_conf, cache=cache)
        old_inner_model = old_model_wrapper.contents
        # logger.info('Loaded old model %s %s', meta['name'], meta['version'])
    except FileNotFoundError:
        logger.info("No old model to load")
        old_inner_model = None

    inner_model = user_mm.create_trained_model(
        model_conf, dso, dsi, old_model=old_inner_model
    )
    m_cls = _get_model_class(complete_conf, cache=cache)
    model_wrapper: ModelInterface = m_cls(contents=inner_model)

    if not isinstance(model_wrapper, ModelInterface):
        logger.warning(
            "Model's class is not a subclass of ModelInterface: %s",
            model_wrapper,
        )

    logger.debug("Testing trained model...")
    metrics = user_mm.test_trained_model(model_conf, dso, dsi, inner_model)

    model_store = _get_model_store(complete_conf, cache=cache)
    model_store.dump_trained_model(complete_conf, model_wrapper, metrics)

    logger.info(
        "Created and stored trained model %s, version %s, metrics %s",
        model_conf["name"],
        model_conf["version"],
        metrics,
    )

    return model_wrapper, metrics


def retest(complete_conf, cache=True):
    """Retest a model as specified in the configuration and persist its
    test metrics in the model store

    Params:
        complete_conf: configuration dict
        cache:         (default: True) whether to cache the data sources/sinks and helper objects (cache lookup is done by model name and model version). If in doubt, leave at default.

    Returns:
        test_metrics
    """
    logger.debug("Retesting existing trained model...")
    user_mm = _get_model_maker(complete_conf, cache=cache)

    dso, dsi = _get_data_sources_and_sinks(
        complete_conf, tags="test", cache=cache
    )

    model_wrapper, metadata = _get_model(complete_conf, cache=cache)
    inner_model = model_wrapper.contents

    model_conf = complete_conf["model"]
    test_metrics = user_mm.test_trained_model(
        model_conf, dso, dsi, inner_model
    )

    model_store = _get_model_store(complete_conf, cache=cache)
    model_store.update_model_metrics(model_conf, test_metrics)

    logger.info(
        "Retested existing model %s, version %s, new metrics %s",
        model_conf["name"],
        model_conf["version"],
        test_metrics,
    )

    return test_metrics


def predict(complete_conf, arg_dict=None, cache=True):
    """Carry out prediction for the model specified in the configuration

    Params:
        complete_conf: configuration dict
        arg_dict:      arguments dict for the prediction (analogous to what it would get from a web API)
        cache:         (default: True) whether to cache the data sources/sinks and helper objects (cache lookup is done by model name and model version). If in doubt, leave at default.

    Returns:
        model's prediction output
    """
    logger.debug("Applying model for prediction...")

    dso, dsi = _get_data_sources_and_sinks(
        complete_conf, tags="predict", cache=cache
    )

    model_wrapper, metadata = _get_model(complete_conf, cache=cache)
    inner_model = model_wrapper.contents

    model_conf = complete_conf["model"]
    output = model_wrapper.predict(
        model_conf, dso, dsi, inner_model, arg_dict or {}
    )
    output = resource.to_plain_python_obj(output)

    return output


def clear_caches():
    global _cached_model_stores
    global _cached_model_tuples
    global _cached_data_source_sink_tuples
    global _cached_model_makers
    global _cached_model_classes

    _cached_model_stores = {}
    _cached_model_tuples = {}
    _cached_data_source_sink_tuples = {}
    _cached_model_makers = {}
    _cached_model_classes = {}


def _model_key(model_conf):
    return model_conf["name"] + "_" + model_conf["version"]


def _find_subclass(module_name, superclass, cache=True):
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
            complete_conf["model"]["module"], ModelMakerInterface, cache=cache
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
            complete_conf["model"]["module"], ModelInterface, cache=cache
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

    key = _model_key(complete_conf["model"])

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
