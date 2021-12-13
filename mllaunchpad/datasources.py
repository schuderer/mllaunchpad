# Stdlib imports
import logging
import os
from typing import Dict, Generator, Iterable, Optional, Union, cast

# Third-party imports
import numpy as np
import pandas as pd

# Project imports
from mllaunchpad.resource import DataSink, DataSource, Raw, get_user_pw


logger = logging.getLogger(__name__)

SUPPORTED_FILE_TYPES = ["csv", "euro_csv", "text_file", "binary_file"]


def get_connection_args(dbms_config: Dict) -> Dict:
    """Fill "_var"-suffixed configuration items from environment variables"""
    if "options" not in dbms_config:
        return {}
    new_options = {}
    key: str
    for key, value in dbms_config["options"].items():
        if key.endswith("_var"):
            new_value = os.environ.get(value)
            if new_value is not None:
                new_key = key[:-4]
                new_options[new_key] = new_value
                logger.debug(
                    "Replaced connection parameter '%s' specifying environment"
                    "variable '%s' with parameter '%s'",
                    key,
                    value,
                    new_key,
                )
            else:
                logger.warning(
                    "Environment variable '%s' not set (from config key '%s'). Leaving it as is.",
                    value,
                    key,
                )
                new_options[key] = value
        else:
            new_options[key] = value

    return new_options


def _get_dict_without_keys(a_dict: Dict, without: Iterable) -> Dict:
    return {k: v for k, v in a_dict.items() if k not in without}


def _create_sqlalchemy_engine(dbms_config: Dict):
    try:
        import sqlalchemy
    except ModuleNotFoundError as e:
        logger.error(
            "Please install the SQLAlchemy package to be able to use SqlDataSource."
        )
        raise e
    connection_string = dbms_config.get("connection_string")
    connect_args = get_connection_args(dbms_config)
    kw_args = _get_dict_without_keys(
        dbms_config, ["type", "options", "connection_string"]
    )
    if "connect_args" in kw_args:
        if connect_args:
            raise ValueError(
                "'options:' (used as 'connect_args') have been specified in "
                "combination with an explicit 'connect_args:'. Please specify "
                "either 'options:' or 'connect_args:', not both."
            )
    else:
        kw_args["connect_args"] = connect_args
    if "url" in kw_args:
        if connection_string:
            raise ValueError(
                "'connection_string:' (used as 'url') has been specified in "
                "combination with an explicit 'url:'. Please specify "
                "either 'connection_string:' or 'url:', not both."
            )
        connection_string = kw_args["url"]
        del kw_args["url"]

    engine = sqlalchemy.create_engine(connection_string, **kw_args)
    return engine


def fill_nas(
    df: pd.DataFrame, as_generator: bool = False
) -> Union[pd.DataFrame, Generator]:
    if as_generator:

        def wrapped_iterator(data):
            for partial_df in data:
                partial_df.fillna(np.nan, inplace=True)
                yield partial_df

        return wrapped_iterator(df)
    else:
        df.fillna(np.nan, inplace=True)
        return df


def ensure_dir_to(file_path):
    path = os.path.dirname(file_path)
    if path != "" and not os.path.exists(path):
        logger.info("Creating missing path to file `{}`.".format(file_path))
        os.makedirs(path)


class SqlDataSource(DataSource):
    """DataSource for RedShift, Postgres, MySQL, SQLite, Oracle, Microsoft SQL (ODBC), and their dialects.

    Uses `SQLAlchemy <https://docs.sqlalchemy.org/>`_ under the hood, and as such, manages a connection pool automatically.

    Please configure the ``dbms:<name>:connection_string:``, which is a standard RFC-1738 URL with the syntax ``dialect[+driver]://[user:password@][host]/[dbname][?key=value..]``.
    The exact URL is specific for the database you want to connect to.
    Find examples for all supported database dialects `here <https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls>`_.

    Depending on the dialect you want to use, you might need to install additional drivers and packages.
    For example, for connecting to a kerberized Impala instance via ODBC, you need to:

    #. Install `Impala ODBC drivers for your OS <https://www.cloudera.com/downloads/connectors/impala/odbc/2-6-10.html>`_,
    #. ``pip install winkerberos thrift_sasl pyodbc sqlalchemy``  # use pykerberos for non-windows systems

    If you are tasked with connecting to a particular database system, and don't know where
    to start, researching on how to connect to it from SQLAlchemy will serve as a good starting point.

    Other configuration in the ``dbms:`` section (besides ``connection_string:``) is optional,
    but can be provided if deemed necessary:

    * Any ``dbms:``-level settings other than ``type:``, ``connection_string:`` and ``options:`` will be passed as additional
      keyword arguments to SQLAlchemy's `create_engine <https://docs.sqlalchemy.org/en/13/core/engines.html#sqlalchemy.create_engine>`_.
    * Any key-value pairs inside ``dbms:<name>:options: {}`` will be passed to SQLAlchemy as `connect_args <https://docs.sqlalchemy.org/en/13/core/engines.html#sqlalchemy.create_engine.params.connect_args>`_.
      If you append ``_var`` to the end of an argument key, its value will be interpreted as an
      environment variable name which ML Launchpad will attempt to get a value from.
      This can be useful for information like passwords which you do not want to store in the configuration file.

    Configuration example::

        dbms:
          # ... (other connections)
          # Example for connecting to a kerberized Impala instance via ODBC:
          my_connection:  # NOTE: You can use the same connection for several datasources and datasinks
            type: sql
            connection_string: mssql+pyodbc:///default?&driver=Cloudera+ODBC+Driver+for+Impala&host=servername.somedomain.com&port=21050&authmech=1&krbservicename=impala&ssl=1&usesasl=1&ignoretransactions=1&usesystemtruststore=1
            # pyodbc alternative: mssql+pyodbc:///?odbc_connect=DRIVER%3D%7BCloudera+ODBC+Driver+for+Impala%7D%3BHOST%3Dservername.somedomain.com%3BPORT%3D21050%3BAUTHMECH%3D1%3BKRBSERVICENAME%3Dimpala%3BSSL%3D1%3BUSESASL%3D1%3BIGNORETRANSACTIONS%3D1%3BUSESYSTEMTRUSTSTORE%3D1
            echo: True  # example for an additional SQLAlchemy keyword argument (logs the SQL) -- these are optional
            options: {}  # used as `connect_args` when creating the SQLAlchemy engine
        # ...
        datasources:
          # ... (other datasources)
          my_datasource:
            type: dbms.my_connection
            query: SELECT * FROM somewhere.my_table WHERE id = :id  # fill `:params` by calling `get_dataframe` with a `dict`
            expires: 0    # generic parameter, see documentation on DataSources
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when fetching the query using `pandas.read_sql`
    """

    serves = ["dbms.sql"]

    def __init__(
        self, identifier: str, datasource_config: Dict, dbms_config: Dict
    ):
        super().__init__(identifier, datasource_config)

        self.dbms_config = dbms_config

        logger.info(
            "Creating database connection engine for datasource {}...".format(
                self.id
            )
        )
        self.engine = _create_sqlalchemy_engine(dbms_config)

    def get_dataframe(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Union[pd.DataFrame, Generator]:
        """Get the data as pandas dataframe.

        Null values are replaced by ``numpy.nan``.

        Example::

            my_df = data_sources["my_datasource"].get_dataframe({"id": 387})

        :param params: Query parameters to fill in query (e.g. replace query's `:id` parameter with value `387`)
        :type params: optional dict
        :param chunksize: Return an iterator where chunksize is the number of rows to include in each chunk.
        :type chunksize: optional int

        :return: DataFrame object, possibly cached according to config value of `expires:`
        """
        # https://stackoverflow.com/questions/53793877/usage-error-in-pandas-read-sql-with-sqlalchemy#comment94441435_53793978
        from sqlalchemy import text

        query = self.config["query"]
        params = params or {}
        kw_options = self.options

        logger.debug(
            "Fetching query {} with params {}, chunksize {}, and options {}...".format(
                query, params, chunksize, kw_options
            )
        )
        df = pd.read_sql(
            text(query),
            con=self.engine,
            params=params,
            chunksize=chunksize,
            **kw_options
        )

        return fill_nas(df, as_generator=chunksize is not None)

    def get_raw(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Raw:
        """Not implemented.

        :raises NotImplementedError: Raw/blob format currently not supported.
        """
        raise NotImplementedError(
            "SqlDataSource currently does not not support raw format/blobs. "
            'Use method "get_dataframe" for dataframes'
        )


class SqlDataSink(DataSink):
    """DataSink for RedShift, Postgres, MySQL, SQLite, Oracle, Microsoft SQL (ODBC), and their dialects.

    Uses `SQLAlchemy <https://docs.sqlalchemy.org/>`_ under the hood, and as such, manages a connection pool automatically.

    Please configure the ``dbms:<name>:connection_string:``, which is a standard RFC-1738 URL with the syntax ``dialect[+driver]://[user:password@][host]/[dbname][?key=value..]``.
    The exact URL is specific for the database you want to connect to.
    Find examples for all supported database dialects `here <https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls>`_.

    Depending on the dialect you want to use, you might need to install additional drivers and packages.
    For example, for connecting to a kerberized Impala instance via ODBC, you need to:

    #. Install `Impala ODBC drivers for your OS <https://www.cloudera.com/downloads/connectors/impala/odbc/2-6-10.html>`_,
    #. ``pip install winkerberos thrift_sasl pyodbc sqlalchemy``  # use pykerberos for non-windows systems

    If you are tasked with connecting to a particular database system, and don't know where
    to start, researching on how to connect to it from SQLAlchemy will serve as a good starting point.

    Other configuration in the ``dbms:`` section (besides ``connection_string:``) is optional,
    but can be provided if deemed necessary:

    * Any ``dbms:``-level settings other than ``type:``, ``connection_string:`` and ``options:`` will be passed as additional
      keyword arguments to SQLAlchemy's `create_engine <https://docs.sqlalchemy.org/en/13/core/engines.html#sqlalchemy.create_engine>`_.
    * Any key-value pairs inside ``dbms:<name>:options: {}`` will be passed to SQLAlchemy as `connect_args <https://docs.sqlalchemy.org/en/13/core/engines.html#sqlalchemy.create_engine.params.connect_args>`_.
      If you append ``_var`` to the end of an argument key, its value will be interpreted as an
      environment variable name which ML Launchpad will attempt to get a value from.
      This can be useful for information like passwords which you do not want to store in the configuration file.

    Configuration example::

        dbms:
          # ... (other connections)
          # Example for connecting to a kerberized Impala instance via ODBC:
          my_connection:  # NOTE: You can use the same connection for several datasources and datasinks
            type: sql
            connection_string: mssql+pyodbc:///default?&driver=Cloudera+ODBC+Driver+for+Impala&host=servername.somedomain.com&port=21050&authmech=1&krbservicename=impala&ssl=1&usesasl=1&ignoretransactions=1&usesystemtruststore=1
            # pyodbc alternative: mssql+pyodbc:///?odbc_connect=DRIVER%3D%7BCloudera+ODBC+Driver+for+Impala%7D%3BHOST%3Dservername.somedomain.com%3BPORT%3D21050%3BAUTHMECH%3D1%3BKRBSERVICENAME%3Dimpala%3BSSL%3D1%3BUSESASL%3D1%3BIGNORETRANSACTIONS%3D1%3BUSESYSTEMTRUSTSTORE%3D1
            echo: True  # example for an additional SQLAlchemy keyword argument (logs the SQL) -- these are optional
            options: {}  # used as `connect_args` when creating the SQLAlchemy engine
        # ...
        datasinks:
          # ... (other datasinks)
          my_datasink:
            type: dbms.my_connection
            table: somewhere.my_table
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when storing the table using `my_df.to_sql`
    """

    serves = ["dbms.sql"]

    def __init__(
        self, identifier: str, datasource_config: Dict, dbms_config: Dict
    ):
        super().__init__(identifier, datasource_config)

        self.dbms_config = dbms_config

        logger.info(
            "Creating database connection engine for datasource {}...".format(
                self.id
            )
        )
        self.engine = _create_sqlalchemy_engine(dbms_config)

    def put_dataframe(
        self,
        dataframe: pd.DataFrame,
        params: Dict = None,
        chunksize: Optional[int] = None,
    ) -> None:
        """Store the pandas dataframe as a table.
        The default is not to store the dataframe's row index.
        Configure the DataSink's options dict to pass keyword arguments to `df.to_sql`.

        Example::

            data_sinks["my_datasink"].put_dataframe(my_df)

        :param dataframe: The pandas dataframe to store
        :type dataframe: pandas DataFrame
        :param params: Currently not implemented
        :type params: optional dict
        :param chunksize: Currently not implemented
        :type chunksize: optional bool
        """
        if params:
            raise NotImplementedError("Parameters not supported yet")
        if chunksize:
            raise NotImplementedError("Buffered storing not supported yet")

        table = self.config["table"]
        kw_options = self.options
        if "index" not in kw_options:
            kw_options["index"] = False

        logger.debug(
            "Storing data in table {} with options {}...".format(
                table, kw_options
            )
        )
        dataframe.to_sql(table, con=self.engine, **kw_options)

    def put_raw(
        self, raw_data, params: Dict = None, chunksize: Optional[int] = None
    ) -> None:
        """Not implemented.

        :raises NotImplementedError: Raw/blob format currently not supported.
        """
        raise NotImplementedError(
            "SqlDataSink currently does not not support raw format/blobs. "
            'Use method "put_dataframe" for raw data'
        )


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
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Union[pd.DataFrame, Generator]:
        """Get the data as pandas dataframe.

        Null values are replaced by ``numpy.nan``.

        Example::

            data_sources["my_datasource"].get_dataframe({"id": 387})

        :param params: Query parameters to fill in query (e.g. replace query's `:id` parameter with value `387`)
        :type params: optional dict
        :param chunksize: Return an iterator where chunksize is the number of rows to include in each chunk.
        :type chunksize: optional int

        :return: DataFrame object, possibly cached according to config value of `expires:`
        """
        # TODO: maybe want to open/close connection on every method call (shouldn't happen often)
        query = self.config["query"]
        params = params or {}
        kw_options = self.options

        logger.debug(
            "Fetching query {} with params {}, chunksize {}, and options {}...".format(
                query, params, chunksize, kw_options
            )
        )
        df = pd.read_sql(
            query,
            con=self.connection,
            params=params,
            chunksize=chunksize,
            **kw_options
        )
        return fill_nas(df, as_generator=chunksize is not None)

    def get_raw(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Raw:
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
            options: {}   # used as **kwargs when storing the table using `my_df.to_sql`
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
        params: Dict = None,
        chunksize: Optional[int] = None,
    ) -> None:
        """Store the pandas dataframe as a table.
        The default is not to store the dataframe's row index.
        Configure the DataSink's options dict to pass keyword arguments to `df.to_sql`.

        Example::

            data_sinks["my_datasink"].put_dataframe(my_df)

        :param dataframe: The pandas dataframe to store
        :type dataframe: pandas DataFrame
        :param params: Currently not implemented
        :type params: optional dict
        :param chunksize: Currently not implemented
        :type chunksize: optional bool
        """
        if params:
            raise NotImplementedError("Parameters not supported yet")
        if chunksize:
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
        self, raw_data, params: Dict = None, chunksize: Optional[int] = None
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
            dtypes_path: ./some/file.dtypes # optional: location with the csv's column dtypes info
          my_raw_datasource:
            type: text_file  # raw files can also be of type `binary_file`
            path: /some/file.txt  # Can be URL
            expires: 0    # generic parameter, see documentation on DataSources
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when fetching the data using `fh.read`

    When loading `csv` or `euro_csv` type formats, you can use the setting `dtypes_path`
    to specify a location with dtypes description for the csv (usually generated earlier
    by using :class:`FileDataSink`'s `dtypes_path` setting). These dtypes will be enforced when
    reading the csv, which helps avoid problems when `pandas.read_csv` interprets data differently than you do.
    Use `dtypes_path` to enforce dtype parity between csv datasinks and datasources.

    Using the raw formats `binary_file` and `text_file`, you can read arbitrary data, as long as
    it can be represented as a `bytes` or a `str` object, respectively. `text_file` uses UTF-8
    encoding. Please note that while possible, it is not
    recommended to persist `DataFrame`s this way, because by adding format-specific code to your
    model, you're giving up your code's independence from the type of `DataSource`/`DataSink`.
    Here's an example for unpickling an arbitrary object::

        # config fragment:
        datasources:
          # ...
          my_pickle_datasource:
            type: binary_file
            path: /some/file.pickle
            tags: [train]
            options: {}

        # code fragment:
        import pickle
        # ...
        # in predict/test/train code:
        my_pickle = data_sources["my_pickle_datasource"].get_raw()
        my_object = pickle.loads(my_pickle)

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
        self.dtypes_path = datasource_config.get("dtypes_path")

    def get_dataframe(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Union[pd.DataFrame, Generator]:
        """Get data as a pandas dataframe.

        Example::

            data_sources["my_datasource"].get_dataframe()

        :param params: Currently not implemented
        :type params: optional dict
        :param chunksize: Return an iterator where chunksize is the number of rows to include in each chunk.
        :type chunksize: optional int

        :return: DataFrame object, possibly cached according to config value of `expires:`
        """
        if params:
            raise NotImplementedError("Parameters not supported yet")

        kw_options = self.options

        logger.debug(
            "Loading type {} file {} with dtypes_path {}, chunksize {} and options {}...".format(
                self.type, self.path, self.dtypes_path, chunksize, kw_options
            )
        )
        if self.dtypes_path is not None:
            input_dtypes = pd.read_csv(self.dtypes_path).set_index("columns")
            kw_options["dtype"] = {
                item: input_dtypes.loc[item]["dtypes"]
                for item in input_dtypes.index
                if input_dtypes.loc[item]["dtypes"] != "datetime"
            }
            kw_options["parse_dates"] = [
                item
                for item in input_dtypes.index
                if input_dtypes.loc[item]["dtypes"] == "datetime"
            ]

        if self.type == "csv":
            df = pd.read_csv(self.path, chunksize=chunksize, **kw_options)
        elif self.type == "euro_csv":
            df = pd.read_csv(
                self.path,
                sep=";",
                decimal=",",
                chunksize=chunksize,
                **kw_options
            )
        else:
            raise TypeError(
                'Can only read csv files as dataframes. Use method "get_raw" for raw data'
            )

        return df

    def get_raw(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Raw:
        """Get data as raw (unstructured) data.

        Example::

            data_sources["my_raw_datasource"].get_raw()

        :param params: Currently not implemented
        :type params: optional dict
        :param chunksize: Currently not implemented
        :type chunksize: optional bool

        :return: The file's bytes (binary) or string (text) contents, possibly cached according to config value of `expires:`
        :rtype: bytes or str
        """
        if params:
            raise NotImplementedError("Parameters not supported yet")
        if chunksize:
            raise NotImplementedError("Buffered reading not supported yet")

        kw_options = self.options

        logger.debug(
            "Loading raw {} {} with options {}...".format(
                self.type, self.path, kw_options
            )
        )

        raw: Raw
        if self.type == "text_file":
            with open(self.path, "r", encoding="utf-8") as txt_file:
                raw = txt_file.read(**kw_options)
        elif self.type == "binary_file":
            with open(self.path, "rb") as bin_file:
                raw = bin_file.read(**kw_options)
        else:
            raise TypeError(
                "Can only read binary data or text strings as raw file. "
                'Use method "get_dataframe" for dataframes'
            )

        return raw


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
            dtypes_path: ./some/file.dtypes # optional: location for saving the csv's column dtypes info
          my_raw_datasink:
            type: text_file  # raw files can also be of type `binary_file`
            path: /some/file.txt  # Can be URL
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
            options: {}   # used as **kwargs when writing the data using `fh.write`

    When saving `csv` or `euro_csv` type formats, you can use the setting `dtypes_path`
    to specify a location where to save dtypes descriptions for the csv (that you can use later
    with :class:`FileDataSource`'s `dtypes_path` setting). These dtypes will be enforced when
    reading the csv, which helps avoid problems when `pandas.read_csv` interprets data differently than you do.
    Use `dtypes_path` to enforce dtype parity between csv datasinks and datasources.

    Using the raw formats `binary_file` and `text_file`, you can persist arbitrary data, as long as
    it can be represented as a `bytes` or a `str` object, respectively. `text_file` uses UTF-8
    encoding. Please note that while possible, it is not
    recommended to persist `DataFrame`s this way, because by adding format-specific code to your
    model, you're giving up your code's independence from the type of `DataSource`/`DataSink`.
    Here's an example for pickling an arbitrary object::

        # config fragment:
        datasinks:
          # ...
          my_pickle_datasink:
            type: binary_file
            path: /some/file.pickle
            tags: [train]
            options: {}

        # code fragment:
        import pickle
        # ...
        # in predict/test/train code:
        my_pickle = pickle.dumps(my_object)
        data_sinks["my_pickle_datasink"].put_raw(my_pickle)
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
        self.dtypes_path = datasink_config.get("dtypes_path")

    def put_dataframe(
        self,
        dataframe: pd.DataFrame,
        params: Dict = None,
        chunksize: Optional[int] = None,
    ) -> None:
        """Write a pandas dataframe to file and optionally the dtypes if included in the configuration.
        The default is not to save the dataframe's row index.
        Configure the DataSink's `options` dict to pass keyword arguments to `my_df.to_csv`.
        If the directory path leading to the file does not exist, it will be created.

        Example::

            data_sinks["my_datasink"].put_dataframe(my_df)

        :param dataframe: The pandas dataframe to save
        :type dataframe: pandas DataFrame
        :param params: Currently not implemented
        :type params: optional dict
        :param chunksize: Currently not implemented
        :type chunksize: optional bool
        """
        if params:
            raise NotImplementedError("Parameters not supported yet")
        if chunksize:
            raise NotImplementedError("Buffered writing not supported yet")

        kw_options = self.options
        if "index" not in kw_options:
            kw_options["index"] = False

        logger.debug(
            "Writing dataframe to type {} file {} with options {} and dtypes_path {}...".format(
                self.type, self.path, kw_options, self.dtypes_path
            )
        )
        if self.dtypes_path:
            dtypes_file = pd.DataFrame(
                dataframe.dtypes, columns=["dtypes"]
            ).rename_axis("columns")
            dtypes_file.loc[
                dtypes_file["dtypes"] == "object", "dtypes"
            ] = "str"
            dtypes_file.loc[
                dtypes_file["dtypes"] == "datetime64[ns]", "dtypes"
            ] = "datetime"
            ensure_dir_to(self.dtypes_path)
            dtypes_file.to_csv(self.dtypes_path)

        if self.type == "csv":
            ensure_dir_to(self.path)
            dataframe.to_csv(self.path, **kw_options)
        elif self.type == "euro_csv":
            ensure_dir_to(self.path)
            dataframe.to_csv(self.path, sep=";", decimal=",", **kw_options)
        else:
            raise TypeError(
                'Can only write dataframes to csv file. Use method "put_raw" for raw data'
            )

    def put_raw(
        self,
        raw_data: Raw,
        params: Dict = None,
        chunksize: Optional[int] = None,
    ) -> None:
        """Write raw (unstructured) data to file.
        If the directory path leading to the file does not exist, it will be created.

        Example::

            data_sinks["my_raw_datasink"].put_raw(my_data)

        :param raw_data: The data to save (bytes for binary, string for text file)
        :type raw_data: bytes or str
        :param params: Currently not implemented
        :type params: optional dict
        :param chunksize: Currently not implemented
        :type chunksize: optional bool
        """
        if params:
            raise NotImplementedError("Parameters not supported yet")
        if chunksize:
            raise NotImplementedError("Buffered writing not supported yet")

        kw_options = self.options

        logger.debug(
            "Writing raw {} file {} with options {}...".format(
                self.type, self.path, kw_options
            )
        )
        if self.type == "text_file":
            if "encoding" not in kw_options:
                kw_options["encoding"] = "utf-8"
            ensure_dir_to(self.path)
            with open(self.path, "w", **kw_options) as txt_file:
                raw_str: str = cast(str, raw_data)
                txt_file.write(raw_str)
        elif self.type == "binary_file":
            ensure_dir_to(self.path)
            with open(self.path, "wb", **kw_options) as bin_file:
                raw_bytes: bytes = cast(bytes, raw_data)
                bin_file.write(raw_bytes)
        else:
            raise TypeError(
                "Can only write binary data or text strings as raw file. "
                + 'Use method "put_dataframe" for dataframes'
            )
