# Stdlib imports
import abc
import getpass
import glob
import json
import logging
import os
import platform
import shutil
import socket
import subprocess  # nosec We are running a known process using its full path (python -m pip).
import sys
from collections import OrderedDict
from datetime import datetime
from time import time
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

# Third-party imports
# We are only unpickling files which are completely under the
# control of the model developer, not influenced by end user data.
import dill as pickle  # nosec
import numpy as np
import pandas as pd

# Project imports
import mllaunchpad as mllp


DS = TypeVar("DS", "DataSource", "DataSink")
Raw = Union[str, bytes]


logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_FILES = "%Y-%m-%d_%H-%M-%S"


class ModelStore:
    """Deals with persisting, loading, updating metrics metadata of models.
    Abstracts away how and where the model is kept.

    TODO: Smarter querying like 'get me the model with the currently (next)
    best metrics which serves a particular API.'
    """

    def __init__(self, config: Union[Dict, str]):
        """Get a model store based on the config settings

        :param config: configuration dict containing the model store location, or model store location as string
        :type complete_conf:  Union[Dict, str]
        """
        if isinstance(config, dict):
            self.location = config["model_store"]["location"]
        else:
            self.location = str(config)
        self.train_report: Dict[str, Any] = {}

    def _ensure_location(self):
        if not os.path.exists(self.location):
            os.makedirs(self.location)

    def _get_model_base_name(self, model_conf):
        return os.path.join(
            self.location,
            "{}_{}".format(model_conf["name"], model_conf["version"]),
        )

    @staticmethod
    def _load_metadata(base_name):
        metadata_name = base_name + ".json"
        with open(metadata_name, "r", encoding="utf-8") as f:
            meta = json.load(f)

        return meta

    @staticmethod
    def _dump_metadata(base_name, raw_metadata):
        metadata_name = base_name + ".json"
        metadata = to_plain_python_obj(raw_metadata)
        try:
            with open(metadata_name, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except TypeError as e:
            os.remove(metadata_name)
            raise e

    def _backup_old_model(self, base_name):
        backup_dir = os.path.join(self.location, "previous")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        infix = datetime.now().strftime(DATE_FORMAT_FILES)
        for file in glob.glob(base_name + "*"):
            fn_ext = os.path.basename(file)
            fn, ext = os.path.splitext(fn_ext)
            new_file_name = "{}_{}{}".format(fn, infix, ext)
            logger.debug(
                "Backing up previous model file {} as {}".format(
                    fn_ext, new_file_name
                )
            )
            shutil.copy(file, os.path.join(backup_dir, new_file_name))

    def dump_trained_model(self, complete_conf, model, metrics):
        """Save a model object in the model store. Some metadata will also
        be saved along the model, including the metrics which is the second parameter.

        Params:
            model_conf:  the config dict of our model
            model:       the model object to store
            metrics:     metrics dictionary

        Returns:
            Nothing
        """
        model_conf = complete_conf["model"]
        base_name = self._get_model_base_name(model_conf)
        self._ensure_location()

        # Check if exists and backup if it does
        self._backup_old_model(base_name)

        # Save model itself
        pkl_name = base_name + ".pkl"
        with open(pkl_name, "wb") as f:
            pickle.dump(model, f)

        # Save metadata
        meta = {
            "name": model_conf["name"],
            "version": model_conf["version"],
            "created": datetime.now().strftime(DATE_FORMAT),
            "created_by": getpass.getuser(),
            "system": {
                "mllaunchpad_version": mllp.__version__,
                "platform": platform.platform(),
                "host": socket.getfqdn(),
                # "host_ip": socket.gethostbyname(socket.getfqdn()),
                "python": sys.version,
                "packages": subprocess.getoutput(
                    "{} -m pip freeze".format(sys.executable)
                ).splitlines(),
            },
            "train_report": self.train_report,
            "metrics": metrics,
            "metrics_history": {datetime.now().strftime(DATE_FORMAT): metrics},
            "config_snapshot": complete_conf,
        }
        if "api" in complete_conf:  # API is optional
            meta["api_base_url"] = mllp.api.get_api_base_url(complete_conf)

        # Add all extra and non-colliding keys in model: section
        for key, val in model_conf.items():
            if key not in meta and key != "module":
                meta[key] = val

        self._dump_metadata(base_name, meta)

    def load_trained_model(self, model_conf):
        """Load a model object from the model store. Some metadata will also
        be loaded along the model.

        Params:
            model_conf:  the config dict of our model

        Returns:
            Tuple of model object and metadata dictionary
        """
        base_name = self._get_model_base_name(model_conf)

        if "." not in sys.path:
            sys.path.append(".")

        pkl_name = base_name + ".pkl"
        with open(pkl_name, "rb") as f:
            # We are only unpickling files which are completely under the
            # control of the model developer, not influenced by end user data.
            model = pickle.load(f)  # nosec

        meta = self._load_metadata(base_name)

        return model, meta

    def update_model_metrics(self, model_conf, metrics):
        """Update the test metrics for a previously stored model
        """
        base_name = self._get_model_base_name(model_conf)
        meta = self._load_metadata(base_name)
        meta["metrics"] = metrics
        meta["metrics_history"][datetime.now().strftime(DATE_FORMAT)] = metrics
        self._dump_metadata(base_name, meta)

    def add_to_train_report(self, name: str, value):
        plain_val = to_plain_python_obj(value)
        self.train_report[name] = plain_val

    def _get_infos_from_json_file(self, file):
        base_name, _ = os.path.splitext(file)
        fn = os.path.basename(base_name)
        fn_parts = fn.split("_")  # there can be more than two
        name = fn_parts[0]
        version = fn_parts[1]
        meta = self._load_metadata(base_name)
        return name, version, meta

    def list_models(self):
        """Get information on all available versions of trained models.

        Side note: This also includes backups of models that have been re-trained without changing
        the version number (they reside in the subdirectory ``previous``).
        Please note that these backed up models are just listed for information and are not available
        for loading (one would have to restore them by moving them up a directory level from ``previous``.

        Example::

            ms = mllp.ModelStore("./model_store")
            all_models = ms.list_models()

            # An example of what a ``list_models()``'s result would look like:
            {
                iris: {
                    1.0.0: { ... complete metadata of this version number ... },
                    1.1.0: { ... },
                    latest: { ... duplicate of metadata of highest available version number, here 1.1.0 ... },
                    backups: [ {...}, {...}, ... ]
                },
                my_other_model: {
                    1.0.1: { ... },
                    2.0.0: { ... },
                    latest: { ... },
                    backups: []
                }
            }

        :returns: Dict with information on all available trained models.
        """

        result = {}
        store_pattern = os.path.join(self.location, "*.json")
        for file in glob.glob(store_pattern):
            name, version, meta = self._get_infos_from_json_file(file)
            result[name] = result.get(name, {})
            result[name][version] = meta

        for name, versions in result.items():
            latest_version_key = max(versions)
            versions["latest"] = versions[latest_version_key]
            result[name]["backups"] = []

        backup_dir = os.path.join(self.location, "previous")
        backup_pattern = os.path.join(backup_dir, "*.json")
        for file in glob.glob(backup_pattern):
            name, version, meta = self._get_infos_from_json_file(file)
            if name in result:
                result[name]["backups"].append(meta)
            else:
                logger.debug(
                    "Ignoring backup for obsolete model %s_%s while collecting model directory",
                    name,
                    version,
                )

        return result


def _tags_match(tags, other_tags) -> bool:
    tags = tags or []
    if isinstance(tags, str):
        tags = [tags]

    other_tags = other_tags or []
    if isinstance(other_tags, str):
        other_tags = [other_tags]

    tags_required = bool(tags)
    tags_provided = bool(other_tags)
    tags_matching = bool(set(tags) & set(other_tags))

    return not tags_required or not tags_provided or tags_matching


def _get_all_classes(config, the_type: Type[DS]) -> Dict[str, Type[DS]]:
    modules = [
        __name__,
        "mllaunchpad.datasources",
    ]  # find built_in types using same mechanism
    if "plugins" in config:
        logger.info("Loading %s plugins", the_type)
        # Append plugins so they can replace builtin types
        modules += config["plugins"]

    ds_cls: Dict[str, Type[DS]] = {}
    for module in modules:
        __import__(module)
        # Handle one import after another so plugins can replace builtin types
        imported_classes = [
            cls
            for cls in the_type.__subclasses__()
            if cls.__module__ == module
        ]
        for cls in imported_classes:
            if hasattr(cls, "serves") and hasattr(cls.serves, "__iter__"):
                for k in cls.serves:
                    if k in ds_cls:
                        logger.warning(
                            f"Plugin class {cls} shadows {ds_cls[k]} which also serves {k}"
                        )
                    ds_cls[k] = cls
                logger.debug(
                    "Loaded %s.%s, serving %s}",
                    module,
                    cls.__name__,
                    cls.serves,
                )
            else:
                logger.warning(f'Class {cls} has no list attribute "serves"')
    return ds_cls


def _create_data_sources_or_sinks(
    config: Dict, the_type: Type[DS], tags: Optional[Iterable[str]] = None
) -> Dict[str, DS]:
    # Implementation note: no generator used because we want to fail early
    if not tags:
        tags = []
    if the_type == DataSource:
        what = "datasource"
        config_key = "datasources"
    elif the_type == DataSink:
        what = "datasink"
        config_key = "datasinks"
    else:
        raise TypeError(
            "`the_type` parameter must be `DataSource` or `DataSink`"
        )
    ds_objects: Dict[str, DS] = {}

    ds_cls: Dict[str, Type[DS]] = _get_all_classes(config, the_type)
    logger.debug("ds_cls=%s", ds_cls)

    if config_key not in config or not isinstance(config[config_key], dict):
        logger.info("No %s defined in configuration", config_key)
        return ds_objects

    for ds_id in config[config_key]:
        ds_config = config[config_key][ds_id]

        if not _tags_match(tags, ds_config.get("tags")):
            continue

        ds_types = ds_config["type"].split(".")
        main_type = ds_types[0]
        sub_type = ds_types[1] if len(ds_types) >= 2 else None
        ds_subtype_config = config[main_type][sub_type] if sub_type else None

        service_need = main_type + (
            "." + ds_subtype_config["type"] if ds_subtype_config else ""
        )

        if service_need not in ds_cls:
            raise ValueError(
                f"No {what} class for {service_need} available. Check the configuration for typos in the {what} type or add a suitable plugin."
            )

        logger.debug(
            "Initializing %s %s of type %s...", what, ds_id, ds_config["type"]
        )
        if ds_subtype_config is None:
            ds_objects[ds_id] = ds_cls[service_need](ds_id, ds_config)
        else:
            ds_objects[ds_id] = ds_cls[service_need](
                ds_id, ds_config, ds_subtype_config
            )

        logger.debug("%s %s initialized", what.capitalize(), ds_id)

    # typing.cast(Dict[str, DS], ds_objects)
    return ds_objects


def create_data_sources_and_sinks(
    config: Dict, tags: Optional[Iterable[str]] = None
) -> Tuple[Dict[str, "DataSource"], Dict[str, "DataSink"]]:
    """Creates the data sources as defined in the configuration dict.
    Filters them by tag.

    Params:
        config: configuration dictionary
        tags:   optionally filter for only matching datasources no value(s) = match all datasources

    Returns:
        dict with keys=datasource names, values=initialized DataSource objects
    """
    if not tags:
        tags = []

    # mypy is unfortunately only accepting instantiable classes here (no ABCs),
    # which is a know issue: https://github.com/python/mypy/issues/5374
    # Ignoring check for now, hoping for a solution/workaround soon.
    sources: Dict[str, DataSource] = _create_data_sources_or_sinks(
        config, the_type=DataSource, tags=tags  # type: ignore
    )
    sinks: Dict[str, DataSink] = _create_data_sources_or_sinks(
        config, the_type=DataSink, tags=tags  # type: ignore
    )

    return sources, sinks


class CacheDict(OrderedDict):
    def __init__(self, *args, **kwds):
        self.maxsize = kwds.pop("maxsize", None)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_size_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.maxsize is not None:
            while len(self) > self.maxsize:
                self.popitem(last=False)

    def __hash__(self):
        return hash(frozenset(self.items()))


class CachedDataSource(type):
    """Metaclass to Auto-apply decorators "@cached" to data getters.
    https://stackoverflow.com/questions/10067262/automatically-decorating-every-instance-method-in-a-class
    """

    def __new__(mcs, name, bases, dct):
        for attr, func in dct.items():
            if attr.startswith("get_"):
                dct[attr] = CachedDataSource.cached(func)
        return type.__new__(mcs, name, bases, dct)

    @classmethod
    def cached(mcs, func):
        """This decorator is automatically applied to `get_dataframe` and `get_raw` methods to enable caching."""

        def wrapper(
            self, params: Dict = None, chunksize: Optional[int] = None
        ):
            if self.expires != 0 and chunksize is not None:
                raise ValueError(
                    'The "chunksize" parameter is incompatible with caching. '
                    'To be able to use "chunksize", please set "expires: 0" '
                    "in the datasource configuration."
                )
            key = (
                func.__name__,
                json.dumps(params, sort_keys=True),
                chunksize,
            )
            item = self._get_cached(key)
            if item is not None:
                return item
            else:
                result = func(self, params, chunksize)
                self._to_cache(key, result)
                return result

        wrapper.__doc__ = func.__doc__
        return wrapper


class DataSource(metaclass=CachedDataSource):
    """Interface, used by the Data Scientist's model to get its data from.
    Concrete DataSources (for files, data bases, etc.) need to inherit from this class.
    """

    serves: List[str] = []

    def __init__(
        self,
        identifier: str,
        datasource_config: Dict,
        sub_config: Optional[Dict] = None,  # used in DBMS subclasses
    ):
        """Please call super().__init(...) when overwriting this method
        """
        self.id = identifier
        self.config = datasource_config
        self.options = self.config.get("options", {})

        self.expires = self.config.get("expires", 0)

        maxsize = self.config.get("cache_size", 32)
        self._cache = CacheDict(maxsize=maxsize)

    @abc.abstractmethod
    def get_dataframe(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Union[pd.DataFrame, Generator]:
        ...

    @abc.abstractmethod
    def get_raw(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Raw:
        ...

    def _get_cached(self, key) -> Any:
        if self.expires == -1 or self.expires > 0:
            item, time_stamp = self._cache.get(key, (None, 0))
            if item is not None and (
                self.expires == -1 or time() <= time_stamp + self.expires
            ):
                logger.debug(
                    "Returning cached item for datasource %s", self.id
                )
                return item
        return None  # either immediately expires (0) or has expired in meantime (>0)

    def _to_cache(self, key, item) -> None:
        if self.expires != 0:
            self._cache[key] = (item, time())

    def __del__(self):
        """Overwrite to clean up any resources (connections, temp files, etc.).
        """
        ...


class DataSink:
    """Interface, used by the Data Scientist's model to persist data (usually prediction results).
    Concrete DataSinks (for files, data bases, etc.) need to inherit from this class.
    """

    serves: List[str] = []

    def __init__(
        self,
        identifier: str,
        datasink_config: Dict,
        sub_config: Optional[Dict] = None,
    ):
        """Please call super().__init(...) when overwriting this method
        """
        self.id = identifier
        self.config = datasink_config
        self.options = self.config.get("options", {})

    @abc.abstractmethod
    def put_dataframe(
        self,
        dataframe: pd.DataFrame,
        params: Dict = None,
        chunksize: Optional[int] = None,
    ) -> None:
        ...

    @abc.abstractmethod
    def put_raw(
        self,
        raw_data: Raw,
        params: Dict = None,
        chunksize: Optional[int] = None,
    ) -> None:
        ...

    def __del__(self):
        """Overwrite to clean up any resources (connections, temp files, etc.).
        """
        ...


def get_user_pw(user_var: str, password_var: str) -> Tuple[str, Optional[str]]:
    user = os.environ.get(user_var)
    pw = os.environ.get(password_var)
    if user is None:
        raise ValueError(
            "User name environment variable {} not set".format(user_var)
        )
    if pw is None:
        logger.warning(
            "Password environment variable %s not set", password_var
        )
    return user, pw


def to_plain_python_obj(possible_ndarray):
    if isinstance(possible_ndarray, dict):
        return {
            key: to_plain_python_obj(val)
            for key, val in possible_ndarray.items()
        }
    if isinstance(possible_ndarray, np.int64):
        return int(possible_ndarray)
    if isinstance(possible_ndarray, np.float32):
        return float(possible_ndarray)
    elif isinstance(possible_ndarray, list) or isinstance(
        possible_ndarray, tuple
    ):
        return [to_plain_python_obj(val) for val in possible_ndarray]
    elif isinstance(possible_ndarray, np.ndarray):
        logger.debug("Automatically converting ndarray to plain python list")
        return possible_ndarray.tolist()
    elif isinstance(possible_ndarray, pd.DataFrame):
        logger.debug("Automatically converting DataFrame to plain python dict")
        return possible_ndarray.to_dict()
    else:
        return possible_ndarray


_order_columns_called = 0


def order_columns(obj: Union[pd.DataFrame, np.ndarray, Dict]):
    """Order the columns of a DataFrame, a dict, or a Numpy structured array.
    Use this on your training data right before passing it into the model.
    This will guarantee that the model is trained with a reproducible column order.

    Same in your test code.

    Most importantly, use this also in your `predict` method, as the incoming
    `args_dict` does not have a deterministic order.

    Params:
        obj: a DataFrame, a dict, or a Numpy structured array

    Returns:
        The `obj` with columns ordered lexicographically
    """
    # Implementation note: not using singledispatch due to necessary checks for all calls regardless of type.
    # try:
    #     caller = sys._getframe().f_back.f_code.co_name
    # except AttributeError:
    #     caller = None
    global _order_columns_called
    _order_columns_called += 1

    if isinstance(obj, pd.DataFrame):
        cols_sorted = sorted(obj.columns.tolist())
        return obj.loc[:, cols_sorted]
    elif isinstance(obj, np.ndarray):
        if obj.dtype.names:
            cols_sorted = sorted(obj.dtype.names)
            return obj[cols_sorted]
        else:
            raise TypeError(
                "Non-structured numpy array does not have column names that can be ordered."
            )
    elif isinstance(obj, dict):
        ordered = OrderedDict(sorted(obj.items()))
        return ordered
    else:
        raise TypeError(
            "`order_columns` called on unsupported type: {}".format(type(obj))
        )
