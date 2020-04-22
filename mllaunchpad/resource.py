# Stdlib imports
import abc
import getpass
import glob
import json
import logging
import os
import shutil
import sys
from collections import OrderedDict
from datetime import datetime
from time import time
from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

# Third-party imports
# We are only unpickling files which are completely under the
# control of the model developer, not influenced by end user data.
import dill as pickle  # nosec
import numpy as np
import pandas as pd


DS = TypeVar("DS", "DataSource", "DataSink")
Raw = Union[str, bytes]


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
        meta = {
            "name": model_conf["name"],
            "version": model_conf["version"],
            "created": datetime.now().strftime(DATE_FORMAT),
            "created_by": getpass.getuser(),
            "metrics": metrics,
            "metrics_history": {datetime.now().strftime(DATE_FORMAT): metrics},
            "config_snapshot": model_conf,
        }
        if "api" in complete_conf:  # API is optional
            meta["api_name"] = complete_conf["api"]["name"]

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
    modules = [__name__]  # find built_in types using same mechanism
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
    config: Dict, the_type: Type[DS], tags: Iterable[str] = []
) -> Dict[str, DS]:
    # Implementation note: no generator used because we want to fail early
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
    config: Dict, tags: Iterable[str] = []
) -> Tuple[Dict[str, "DataSource"], Dict[str, "DataSink"]]:
    """Creates the data sources as defined in the configuration dict.
    Filters them by tag.

    Params:
        config: configuration dictionary
        tags:   optionally filter for only matching datasources no value(s) = match all datasources

    Returns:
        dict with keys=datasource names, values=initialized DataSource objects
    """

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


class DataSource:
    """Interface, used by the Data Scientist's model to get its data from.
    Concrete DataSources (for files, data bases, etc.) need to inherit from this class.
    """

    serves: List[str] = []

    def __init__(
        self,
        identifier: str,
        datasource_config: Dict,
        sub_config: Optional[Dict] = None,
    ):
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

    @abc.abstractmethod
    def get_dataframe(
        self, arg_dict: Dict = None, buffer: bool = False
    ) -> pd.DataFrame:
        ...

    @abc.abstractmethod
    def get_raw(self, arg_dict: Dict = None, buffer: bool = False) -> Raw:
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


def _get_oracle_connection(dbms_config: Dict):
    import cx_Oracle  # Importing here avoids environment-specific dependencies

    user, pw = get_user_pw(
        dbms_config["user_var"], dbms_config["password_var"]
    )
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
    """DataSource for Oracle database connections.

    Creates a long-living connection on initialization.

    Configuration example::

        dbms:
          # ... (other connections)
          my_connection:  # NOTE: You can use the same connection for several datasources and datasinks
            type: oracle
            host: host.example.com
            port: 1251
            user_var: MY_USER_ENV_VAR
            password_var: MY_PW_ENV_VAR  # optional
            service_name: servicename.example.com
            options: {}  # used as **kwargs when initializing the DB connection
        # ...
        datasources:
          # ... (other datasources)
          my_datasource:
            type: dbms.my_connection
            query: SELECT * FROM somewhere.my_table where id = :id  # fill `:params` by calling `get_dataframe` with a `dict`
            expires: 0    # generic parameter, see documentation on DataSources
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when fetching the query using `pandas.read_sql`
    """

    serves = ["dbms.oracle"]

    def __init__(
        self, identifier: str, datasource_config: Dict, dbms_config: Dict
    ):
        super().__init__(identifier, datasource_config)

        self.dbms_config = dbms_config

        logger.info(
            "Establishing Oracle database connection for datasource {}...".format(
                self.id
            )
        )
        self.connection = _get_oracle_connection(dbms_config)

    def get_dataframe(
        self, arg_dict: Dict = None, buffer: bool = False
    ) -> pd.DataFrame:
        """Get the data as pandas dataframe.

        Example::

            data_sources["my_datasource"].get_dataframe({"id": 387})

        :param arg_dict: Query parameters to fill in query (e.g. replace query's `:id` parameter with value `387`)
        :type arg_dict: optional dict
        :param buffer: Currently not implemented
        :type buffer: optional bool

        :return: DataFrame object, possibly cached according to config value of `expires:`
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
        df.fillna(np.nan, inplace=True)

        self._cache_df_if_required(df)

        return df

    def get_raw(self, arg_dict: Dict = None, buffer: bool = False) -> Raw:
        """Not implemented.

        :raises NotImplementedError: Raw/blob format currently not supported.
        """
        raise NotImplementedError(
            "OracleDataSource currently does not not support raw format/blobs. "
            'Use method "get_dataframe" for dataframes'
        )

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()


class FileDataSource(DataSource):
    """DataSource for fetching data from files.

    See :attr:`serves` for the available types.

    Configuration example::

        datasources:
          # ... (other datasources)
          my_datasource:
            type: euro_csv  # `euro_csv` changes separators to ";" and decimals to "," w.r.t. `csv`
            path: /some/file.csv  # Can be URL, uses `pandas.read_csv` internally
            expires: 0    # generic parameter, see documentation on DataSources
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when fetching the data using `pandas.read_csv`
          my_raw_datasource:
            type: text_file  # raw files can also be of type `binary_file`
            path: /some/file.txt  # Can be URL
            expires: 0    # generic parameter, see documentation on DataSources
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when fetching the data using `fh.read`
    """

    serves = SUPPORTED_FILE_TYPES

    def __init__(self, identifier: str, datasource_config: Dict):
        super().__init__(identifier, datasource_config)

        ds_type = datasource_config["type"]
        if ds_type not in SUPPORTED_FILE_TYPES:
            raise TypeError(
                "{} is not a datasource file type (in datasource {}).".format(
                    repr(ds_type), repr(identifier)
                )
            )

        self.type = ds_type
        self.path = datasource_config["path"]

    def get_dataframe(
        self, arg_dict: Dict = None, buffer: bool = False
    ) -> pd.DataFrame:
        """Get data as a pandas dataframe.

        Example::

            data_sources["my_datasource"].get_dataframe()

        :param arg_dict: Currently not implemented
        :type arg_dict: optional dict
        :param buffer: Currently not implemented
        :type buffer: optional bool

        :return: DataFrame object, possibly cached according to config value of `expires:`
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
            raise TypeError(
                'Can only read csv files as dataframes. Use method "get_raw" for raw data'
            )

        self._cache_df_if_required(df)

        return df

    def get_raw(self, arg_dict: Dict = None, buffer: bool = False) -> Raw:
        """Get data as raw (unstructured) data.

        Example::

            data_sources["my_raw_datasource"].get_raw()

        :param arg_dict: Currently not implemented
        :type arg_dict: optional dict
        :param buffer: Currently not implemented
        :type buffer: optional bool

        :return: The file's bytes (binary) or string (text) contents, possibly cached according to config value of `expires:`
        :rtype: bytes or str
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

        raw: Raw
        if self.type == "text_file":
            with open(self.path, "r") as txt_file:
                raw = txt_file.read(**kw_options)
        elif self.type == "binary_file":
            with open(self.path, "rb") as bin_file:
                raw = bin_file.read(**kw_options)
        else:
            raise TypeError(
                "Can only read binary data or text strings as raw file. "
                'Use method "get_dataframe" for dataframes'
            )

        self._cache_raw_if_required(raw)
        return raw


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
        self, dataframe: pd.DataFrame, arg_dict=None, buffer=False
    ) -> None:
        ...

    @abc.abstractmethod
    def put_raw(self, raw_data: Raw, arg_dict=None, buffer=False) -> None:
        ...

    def __del__(self):
        """Overwrite to clean up any resources (connections, temp files, etc.).
        """
        ...


class FileDataSink(DataSink):
    """DataSink for putting data into files.

    See :attr:`serves` for the available types.

    Configuration example::

        datasinks:
          # ... (other datasinks)
          my_datasink:
            type: euro_csv  # `euro_csv` changes separators to ";" and decimals to "," w.r.t. `csv`
            path: /some/file.csv  # Can be URL, uses `df.to_csv` internally
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when fetching the data using `df.to_csv`
          my_raw_datasink:
            type: text_file  # raw files can also be of type `binary_file`
            path: /some/file.txt  # Can be URL
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when writing the data using `fh.write`
    """

    serves = SUPPORTED_FILE_TYPES

    def __init__(self, identifier: str, datasink_config: Dict):
        super().__init__(identifier, datasink_config)

        ds_type = datasink_config["type"]
        if ds_type not in SUPPORTED_FILE_TYPES:
            raise TypeError(
                "{} is not a datasink file type (in datasink {}).".format(
                    repr(ds_type), repr(identifier)
                )
            )

        self.type = ds_type
        self.path = datasink_config["path"]

    def put_dataframe(
        self,
        dataframe: pd.DataFrame,
        arg_dict: Dict = None,
        buffer: bool = False,
    ) -> None:
        """Write a pandas dataframe to file.
        The default is not to save the dataframe's row index.
        Configure the DataSink's `options` dict to pass keyword arguments to `my_df.to_csv`.

        Example::

            data_sinks["my_datasink"].put_dataframe(my_df)

        :param dataframe: The pandas dataframe to save
        :type dataframe: pandas DataFrame
        :param arg_dict: Currently not implemented
        :type arg_dict: optional dict
        :param buffer: Currently not implemented
        :type buffer: optional bool
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
            raise TypeError(
                'Can only write dataframes to csv file. Use method "put_raw" for raw data'
            )

    def put_raw(
        self, raw_data: Raw, arg_dict: Dict = None, buffer: bool = False,
    ) -> None:
        """Write raw (unstructured) data to file.

        Example::

            data_sinks["my_raw_datasink"].put_raw(my_data)

        :param raw_data: The data to save (bytes for binary, string for text file)
        :type raw_data: bytes or str
        :param arg_dict: Currently not implemented
        :type arg_dict: optional dict
        :param buffer: Currently not implemented
        :type buffer: optional bool
        """
        if buffer:
            raise NotImplementedError("Buffered writing not supported yet")

        kw_options = self.options

        logger.debug(
            "Writing raw {} file {} with options {}...".format(
                self.type, self.path, kw_options
            )
        )
        if self.type == "text_file":
            with open(self.path, "w", **kw_options) as txt_file:
                raw_str: str = cast(str, raw_data)
                txt_file.write(raw_str)
        elif self.type == "binary_file":
            with open(self.path, "wb", **kw_options) as bin_file:
                raw_bytes: bytes = cast(bytes, raw_data)
                bin_file.write(raw_bytes)
        else:
            raise TypeError(
                "Can only write binary data or text strings as raw file. "
                + 'Use method "put_dataframe" for dataframes'
            )


class OracleDataSink(DataSink):
    """DataSink for Oracle database connections.

    Creates a long-living connection on initialization.

    Configuration example::

        dbms:
          # ... (other connections)
          my_connection:  # NOTE: You can use the same connection for several datasources and datasinks
            type: oracle
            host: host.example.com
            port: 1251
            user_var: MY_USER_ENV_VAR
            password_var: MY_PW_ENV_VAR  # optional
            service_name: servicename.example.com
            options: {}  # used as **kwargs when initializing the DB connection
        # ...
        datasinks:
          # ... (other datasinks)
          my_datasink:
            type: dbms.my_connection
            table: somewhere.my_table
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when fetching the query using `pandas.to_sql`
    """

    serves = ["dbms.oracle"]

    def __init__(
        self, identifier: str, datasink_config: Dict, dbms_config: Dict
    ):
        super().__init__(identifier, datasink_config)

        self.dbms_config = dbms_config

        logger.info(
            "Establishing Oracle database connection for datasource {}...".format(
                self.id
            )
        )

        self.connection = _get_oracle_connection(dbms_config)

    def put_dataframe(
        self,
        dataframe: pd.DataFrame,
        arg_dict: Dict = None,
        buffer: bool = False,
    ) -> None:
        """Store the pandas dataframe as a table.
        The default is not to store the dataframe's row index.
        Configure the DataSink's options dict to pass keyword arguments to `df.o_sql`.

        Example::

            data_sinks["my_datasink"].put_dataframe(my_df)

        :param dataframe: The pandas dataframe to store
        :type dataframe: pandas DataFrame
        :param arg_dict: Currently not implemented
        :type arg_dict: optional dict
        :param buffer: Currently not implemented
        :type buffer: optional bool
        """
        if buffer:
            raise NotImplementedError("Buffered storing not supported yet")

        # TODO: maybe want to open/close connection on every method call (shouldn't happen often)
        table = self.config["table"]
        kw_options = self.options
        if "index" not in kw_options:
            kw_options["index"] = False

        logger.debug(
            "Storing data in table {} with options {}...".format(
                table, kw_options
            )
        )
        dataframe.to_sql(table, con=self.connection, **kw_options)

    def put_raw(
        self, raw_data, arg_dict: str = None, buffer: bool = False
    ) -> None:
        """Not implemented.

        :raises NotImplementedError: Raw/blob format currently not supported.
        """
        raise NotImplementedError(
            "OracleDataSink currently does not not support raw format/blobs. "
            'Use method "put_dataframe" for raw data'
        )

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()


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
