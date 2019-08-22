# -*- coding: utf-8 -*-

# Stdlib imports
from datetime import datetime
import getpass
import glob
import json
import logging
import os
import shutil
import sys
from time import time
import typing
from typing import Dict, Tuple, Type, TypeVar, Union

# Third-party imports
import dill as pickle
import numpy as np
import pandas as pd

DS = TypeVar("DS", "DataSource", "DataSink")

logger = logging.getLogger(__name__)

SUPPORTED_FILE_TYPES = ["csv", "euro_csv", "text_file", "binary_file"]
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_FILES = "%Y-%m-%d_%H-%M-%S"


class ModelStore:
    """Deals with persisting, loading, updating metrics metadata of models.
    Abstracts away how and where the model is kept.

    TODO: Smarter querying like 'get me the model with the currently (next)
    best metrics which serves a particular API.'
    """

    def __init__(self, config):
        """Get a model store based on the config settings

        Params:
            config: configuration dict
        """
        self.location = config["model_store"]["location"]
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
        with open(metadata_name, "r") as f:
            meta = json.load(f)

        return meta

    @staticmethod
    def _dump_metadata(base_name, raw_metadata):
        metadata_name = base_name + ".json"
        metadata = to_plain_python_obj(raw_metadata)
        try:
            with open(metadata_name, "w") as f:
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

        # Check if exists and backup if it does
        self._backup_old_model(base_name)

        # Save model itself
        pkl_name = base_name + ".pkl"
        with open(pkl_name, "wb") as f:
            pickle.dump(model, f)

        # Save metadata
        api_conf = complete_conf["api"]
        meta = {
            "name": model_conf["name"],
            "version": model_conf["version"],
            "api_name": api_conf["name"],
            "api_version": api_conf["version"],
            "created": datetime.now().strftime(DATE_FORMAT),
            "created_by": getpass.getuser(),
            "metrics": metrics,
            "metrics_history": {datetime.now().strftime(DATE_FORMAT): metrics},
            "config_snapshot": model_conf,
        }
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
            model = pickle.load(f)

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


def _tags_match(tags, other_tags) -> bool:
    tags = tags or []
    if type(tags) is str:
        tags = [tags]

    other_tags = other_tags or []
    if type(other_tags) is str:
        other_tags = [other_tags]

    tags_required = bool(tags)
    tags_provided = bool(other_tags)
    tags_matching = bool(set(tags) & set(other_tags))

    return not tags_required or not tags_provided or tags_matching


def _get_all_classes(config, the_type: Type[Union["DataSource", "DataSink"]]):
    modules = [__name__]  # find built_in types using same mechanism
    if "plugins" in config:
        logger.info("Loading %s plugins", the_type)
        # Append plugins so they can replace builtin types
        modules += config["plugins"]

    ds_cls = {}
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
    config, the_type: Type[Union["DataSource", "DataSink"]], tags=None
) -> Dict[str, Union["DataSource", "DataSink"]]:
    # Implementation note: no generator used because we want to fail early
    ds_objects: Dict[DS] = {}

    if the_type == DataSource:
        what = "datasource"
        config_key = "datasources"
    else:  # datasource_or_datasink == DataSink:
        what = "datasink"
        config_key = "datasinks"

    ds_cls = _get_all_classes(config, the_type)
    logger.debug("ds_cls=%s", ds_cls)

    if config_key not in config or type(config[config_key]) is not dict:
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

        logger.debug("Datasource %s initialized", ds_id)

    typing.cast(Dict[str, the_type], ds_objects)
    return ds_objects


def create_data_sources_and_sinks(
    config, tags=None
) -> Tuple[Dict[str, "DataSource"], Dict[str, "DataSink"]]:
    """Creates the data sources as defined in the configuration dict.
    Filters them by tag.

    Params:
        config: configuration dictionary
        tags:   optionally filter for only matching datasources no value(s) = match all datasources

    Returns:
        dict with keys=datasource names, values=initialized DataSource objects
    """

    sources: Dict[str, DataSource] = _create_data_sources_or_sinks(
        config, the_type=DataSource, tags=tags
    )
    sinks: Dict[str, DataSink] = _create_data_sources_or_sinks(
        config, the_type=DataSink, tags=tags
    )

    return sources, sinks


class DataSource:
    """Interface, used by the Data Scientist's model to get its data from.
    Concrete DataSources (for files, data bases, etc.) need to inherit from this class.
    """

    serves = []

    def __init__(self, identifier, datasource_config):
        """Please call super().__init(...) when overwriting this method
        """
        self.id = identifier
        self.config = datasource_config
        self.options = self.config.get("options", {})

        self.expires = self.config.get("expires", 0)

        self._cached_df = None
        self._cached_df_time = 0
        self._cached_raw = None
        self._cached_raw_time = 0

    def get_dataframe(self, arg_dict=None, buffer=False) -> pd.DataFrame:
        ...

    def get_raw(self, arg_dict=None, buffer=False) -> bytes:
        ...

    def _try_get_cached_df(self):
        if self._cached_df is not None and (
            self.expires == -1  # cache indefinitely
            or (
                self.expires > 0
                and time() <= self._cached_df_time + self.expires
            )
        ):
            logger.debug(
                "Returning cached dataframe for datasource %s", self.id
            )
            return self._cached_df
        else:  # either immediately expires (0) or has expired in meantime (>0)
            return None

    def _try_get_cached_raw(self):
        if self._cached_raw is not None and (
            self.expires == -1  # cache indefinitely
            or (
                self.expires > 0
                and time() <= self._cached_raw_time + self.expires
            )
        ):
            logger.debug(
                "Returning cached raw data for datasource %s", self.id
            )
            return self._cached_raw
        else:  # either immediately expires (0) or has expired in meantime (>0)
            return None

    def _cache_df_if_required(self, df):
        if self.expires != 0:
            self._cached_df_time = time()
            self._cached_df = df

    def _cache_raw_if_required(self, raw):
        if self.expires != 0:
            self._cached_raw_time = time()
            self._cached_raw = raw

    def __del__(self):
        """Overwrite to clean up any resources (connections, temp files, etc.).
        """
        ...


def get_user_pw(dbms_config):
    user_var_name = dbms_config["user_var"]
    pw_var_name = dbms_config["password_var"]
    user = os.environ.get(user_var_name)
    pw = os.environ.get(pw_var_name)
    if user is None:
        raise ValueError(
            "User name environment variable {} not set".format(user_var_name)
        )
    if pw is None:
        logger.warning("Password environment variable %s not set", pw_var_name)
    return user, pw


def get_oracle_connection(dbms_config):
    import cx_Oracle  # Importing here avoids environment-specific dependencies

    user, pw = get_user_pw(dbms_config)
    dsn_tns = cx_Oracle.makedsn(
        dbms_config["host"],
        dbms_config["port"],
        service_name=dbms_config["service_name"],
    )
    logger.debug("Oracle connection string: %s", dsn_tns)

    kw_options = dbms_config.get("options", {})
    connection = cx_Oracle.connect(user, pw, dsn_tns, **kw_options)

    return connection


class OracleDataSource(DataSource):
    """DataSource for Oracle database connections
    """

    serves = ["dbms.oracle"]

    def __init__(self, identifier, datasource_config, dbms_config):
        super().__init__(identifier, datasource_config)

        self.dbms_config = dbms_config

        logger.info(
            "Establishing Oracle database connection for datasource {}...".format(
                self.id
            )
        )
        self.connection = get_oracle_connection(dbms_config)

    def get_dataframe(self, arg_dict=None, buffer=False):
        """Get the FileDataSource's data as pandas dataframe.
        Configure the DataSource's options dict to pass keyword arguments to panda's read_sql.

        Params:
            args_dict: optional, parameters for SQL stored procedure
            buffer: optional, currently not implemented

        Returns:
            DataFrame object, possibly cached according to expires-config
        """
        if buffer:
            raise NotImplementedError("Buffered reading not supported yet")

        cached = self._try_get_cached_df()
        if cached is not None:
            return cached

        # TODO: maybe want to open/close connection on every method call (shouldn't happen often)
        query = self.config["query"]
        params = arg_dict or {}
        kw_options = self.options

        logger.debug(
            "Fetching query {} with params {} and options {}...".format(
                query, params, kw_options
            )
        )
        df = pd.read_sql(
            query, con=self.connection, params=params, **kw_options
        )

        self._cache_df_if_required(df)

        return df

    def get_raw(self, arg_dict=None, buffer=False):
        """Not implemented"""
        raise TypeError(
            "OracleDataSource currently does not not support raw format/blobs"
        )

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()


class FileDataSource(DataSource):
    """DataSource for fetching data from files
    """

    serves = SUPPORTED_FILE_TYPES

    def __init__(self, identifier, datasource_config):
        super().__init__(identifier, datasource_config)

        ds_type = datasource_config["type"]
        if ds_type not in SUPPORTED_FILE_TYPES:
            raise ValueError(
                "{} is not a datasource file type (in datasource {}).".format(
                    repr(ds_type), repr(identifier)
                )
            )

        self.type = ds_type
        self.path = datasource_config["path"]

    def get_dataframe(self, arg_dict=None, buffer=False):
        """Get the FileDataSource's data as pandas dataframe.
        Configure the DataSource's options dict to pass keyword arguments to panda's read_csv.

        Params:
            args_dict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            DataFrame object, possibly cached according to expires-config
        """
        if buffer:
            raise NotImplementedError("Buffered reading not supported yet")

        cached = self._try_get_cached_df()
        if cached is not None:
            return cached

        kw_options = self.options

        logger.debug(
            "Loading type {} file {} with options {}...".format(
                self.type, self.path, kw_options
            )
        )
        if self.type == "csv":
            df = pd.read_csv(self.path, **kw_options)
        elif self.type == "euro_csv":
            df = pd.read_csv(self.path, sep=";", decimal=",", **kw_options)
        else:
            raise ValueError(
                'Can only read csv files as dataframes. Use method "get_raw" for raw data'
            )

        self._cache_df_if_required(df)

        return df

    def get_raw(self, arg_dict=None, buffer=False):
        """Get the FileDataSource's data as raw binary data.

        Params:
            args_dict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            The file's bytes (binary) or string (text) contents,
            possibly cached according to expires-config
        """
        if buffer:
            raise NotImplementedError("Buffered reading not supported yet")

        cached = self._try_get_cached_raw()
        if cached is not None:
            return cached

        kw_options = self.options

        logger.debug(
            "Loading raw {} {} with options {}...".format(
                self.type, self.path, kw_options
            )
        )
        if self.type == "text_file":
            with open(self.path, "r") as txt_file:
                raw = txt_file.read(**kw_options)
        elif self.type == "binary_file":
            with open(self.path, "rb") as bin_file:
                raw = bin_file.read(**kw_options)
        else:
            raise ValueError(
                "Can only read binary data or text strings as raw file. "
                + 'Use method "get_dataframe" for dataframes'
            )

        self._cache_raw_if_required(raw)

        return raw


class DataSink:
    """Interface, used by the Data Scientist's model to persist data (usually prediction results).
    Concrete DataSinks (for files, data bases, etc.) need to inherit from this class.
    """

    serves = []

    def __init__(self, identifier, datasink_config):
        """Please call super().__init(...) when overwriting this method
        """
        self.id = identifier
        self.config = datasink_config
        self.options = self.config.get("options", {})

    def put_dataframe(
        self, dataframe: pd.DataFrame, arg_dict=None, buffer=False
    ):
        ...

    def put_raw(
        self, raw_data: Union[bytes, str], arg_dict=None, buffer=False
    ):
        ...

    def __del__(self):
        """Overwrite to clean up any resources (connections, temp files, etc.).
        """
        ...


class FileDataSink(DataSink):
    """DataSource for fetching data from files
    """

    serves = SUPPORTED_FILE_TYPES

    def __init__(self, identifier, datasink_config):
        super().__init__(identifier, datasink_config)

        ds_type = datasink_config["type"]
        if ds_type not in SUPPORTED_FILE_TYPES:
            raise ValueError(
                "{} is not a datasink file type (in datasink {}).".format(
                    repr(ds_type), repr(identifier)
                )
            )

        self.type = ds_type
        self.path = datasink_config["path"]

    def put_dataframe(self, dataframe, arg_dict=None, buffer=False):
        """Write a pandas dataframe to file.
        The default is not to save the dataframe's row index.
        Configure the DataSink's options dict to pass keyword arguments to panda's to_csv.

        Params:
            dataframe: the pandas dataframe to save
            args_dict: optional, currently not implemented
            buffer: optional, currently not implemented
        """
        if buffer:
            raise NotImplementedError("Buffered writing not supported yet")

        kw_options = self.options
        if "index" not in kw_options:
            kw_options["index"] = False

        logger.debug(
            "Writing dataframe to type {} file {} with options {}...".format(
                self.type, self.path, kw_options
            )
        )
        if self.type == "csv":
            dataframe.to_csv(self.path, **kw_options)
        elif self.type == "euro_csv":
            dataframe.to_csv(self.path, sep=";", decimal=",", **kw_options)
        else:
            raise ValueError(
                'Can only write dataframes to csv file. Use method "put_raw" for raw data'
            )

    def put_raw(self, raw_data, arg_dict=None, buffer=False):
        """Write raw data to file.

        Params:
            raw_data: the data to save (bytes for binary, string for text file)
            args_dict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            The file's bytes, possibly cached according to expires-config
        """
        if buffer:
            raise NotImplementedError("Buffered writing not supported yet")

        kw_options = self.options

        logger.debug(
            "Writing raw binary file {} with options {}...".format(
                self.type, self.path, kw_options
            )
        )
        if self.type == "text_file":
            with open(self.path, "w", **kw_options) as txt_file:
                txt_file.write(raw_data)
        elif self.type == "binary_file":
            with open(self.path, "wb", **kw_options) as bin_file:
                bin_file.write(raw_data)
        else:
            raise ValueError(
                "Can only write binary data or text strings as raw file. "
                + 'Use method "get_dataframe" for dataframes'
            )


class OracleDataSink(DataSink):
    """DataSink for Oracle database connections
    """

    serves = ["dbms.oracle"]

    def __init__(self, identifier, datasink_config, dbms_config):
        super().__init__(identifier, datasink_config)

        self.dbms_config = dbms_config

        logger.info(
            "Establishing Oracle database connection for datasource {}...".format(
                self.id
            )
        )

        self.connection = get_oracle_connection(dbms_config)

    def put_dataframe(self, dataframe, arg_dict=None, buffer=False):
        """Store the pandas dataframe as a table.
        The default is not to store the dataframe's row index.
        Configure the DataSink's options dict to pass keyword arguments to panda's to_sql.

        Params:
            dataframe: the pandas dataframe to store
            args_dict: optional, currently not implemented
            buffer: optional, currently not implemented
        """
        if buffer:
            raise NotImplementedError("Buffered storing not supported yet")

        # TODO: maybe want to open/close connection on every method call (shouldn't happen often)
        query = self.config["table"]
        kw_options = self.options
        if "index" not in kw_options:
            kw_options["index"] = False

        logger.debug(
            "Storing data in table {} with options {}...".format(
                query, kw_options
            )
        )
        dataframe.to_sql(query, con=self.connection, **kw_options)

    def put_raw(self, raw_data, arg_dict=None, buffer=False):
        """Not implemented"""
        raise TypeError(
            "OracleDataSink currently does not not support raw format/blobs"
        )

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()


def to_plain_python_obj(possible_ndarray):
    if type(possible_ndarray) is dict:
        return {
            key: to_plain_python_obj(val)
            for key, val in possible_ndarray.items()
        }
    if type(possible_ndarray) is np.int64:
        return int(possible_ndarray)
    if type(possible_ndarray) is np.float32:
        return float(possible_ndarray)
    elif type(possible_ndarray) is list or type(possible_ndarray) is tuple:
        return [to_plain_python_obj(val) for val in possible_ndarray]
    elif type(possible_ndarray) is np.ndarray:
        logger.debug("Automatically converting ndarray to plain python list")
        return possible_ndarray.tolist()
    elif type(possible_ndarray) is pd.DataFrame:
        logger.debug("Automatically converting DataFrame to plain python dict")
        return possible_ndarray.to_dict()
    else:
        return possible_ndarray
