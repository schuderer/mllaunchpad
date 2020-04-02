import logging
import os

import pandas as pd

from mllaunchpad.resource import DataSource


logger = logging.getLogger(__name__)

try:
    from impala.dbapi import connect
except ModuleNotFoundError:
    logger.warning("Please install the impyla package to be able to use ImpalaDataSource.")


class ImpalaDataSource(DataSource):
    """DataSource for fetching data from Impala queries.

    EXPERIMENTAL

    Creates a short-lived connection on every non-cached call to `get_dataframe`.

    Configuration::

        dbms:
          # ... (other connections)
          my_connection:  # NOTE: You can use the same connection for several datasources and datasinks
            type: impala
            # NOTE: The options below are examples for accessing a kerberized cluster.
            #       You can specify other options here, and they will be used for creating
            #       the connection. For a full list, refer to the documentation of
            #       `impyla.dbapi.connect`: https://pydoc.net/impyla/0.14.0/impala.dbapi/
            # NOTE 2: For user and password parameters, you can provide the parameter with
            #         the suffix "_var". For example, if you configure `ldap_password_var: MY_PW`,
            #         ML Launchpad will get the value of the environment variable `MY_PW` and pass
            #         it to `impyla.dbapi.connect`s `ldap_password` parameter. This is to avoid
            #         having to add passwords to the configuration file.
            host: host.example.com
            port: 21050
            database: my_db
            kerberos_service_name: impala
            auth_mechanism: GSSAPI
            use_ssl: true
        # ...
        datasources:
          # ... (other datasources)
          my_datasource:
            type: dbms.my_connection
            query: SELECT * FROM my_table where id = :id  # fill `:params` by calling `get_dataframe` with a `dict`
            expires: 0     # generic parameter, see documentation on DataSources
            tags: [train]  # generic parameter, see documentation on DataSources and DataSinks
            options: {}    # (optional) any other kwargs to pass to `pd.read_sql`

    Note: In order to access a kerberized cluster, you need the correct packages.
    We found the following packages to work reliably::

        $ pip install pykerberos thrift_sasl impyla pandas
        (for Windows, use winkerberos instead of pykerberos)
    """
    serves = ['dbms.impala']

    def __init__(self, identifier, datasink_config, dbms_config):
        super().__init__(identifier, datasink_config)

        # Fill "_var"-suffixed configuration items from environment variables
        new_dbms_config = {}
        key: str
        for key, value in dbms_config.items():
            if key.endswith("_var"):
                new_value = os.environ.get(value)
                if new_value is not None:
                    new_key = key[:-4]
                    new_dbms_config[new_key] = new_value
                    logger.debug("Replaced Impala connection parameter '%s' specifying environment"
                                 "variable '%s' with parameter '%s'", key, value, new_key)
                else:
                    logger.warning("Environment variable '%s' not set (from config key '%s')", value, key)
                    new_dbms_config[key] = value
            else:
                new_dbms_config[key] = value

        self.dbms_config = new_dbms_config

    def get_dataframe(self, arg_dict=None, buffer=False):
        """Get data as a pandas dataframe.

        Example::

            data_sources["my_datasource"].get_dataframe({"id": 387})

        :param arg_dict: Query parameters to fill in query (e.g. `:id` with value 387)
        :type arg_dict: optional dict
        :param buffer: Currently not implemented
        :type buffer: optional bool

        :return: DataFrame object, possibly cached according to expires-config
        """
        if buffer:
            raise NotImplementedError('Buffered reading not supported yet')

        cached = self._try_get_cached_df()
        if cached is not None:
            return cached

        # Open connection
        logger.info(
            "Establishing Impala database connection for datasource {}...".format(
                self.id
            )
        )
        conn_args = {k: v for k, v in self.dbms_config.items() if k not in ["type"]}
        with connect(**conn_args) as conn:
            # Fetch query
            query = self.config["query"]
            params = arg_dict or {}
            kw_options = self.config.get("options", {})
            logger.debug(
                "Fetching query {} with params {} and options {}...".format(
                    query, params, kw_options
                )
            )
            df = pd.read_sql(
                query, con=conn, params=params, **kw_options
            )

        self._cache_df_if_required(df)

        return df

    def get_raw(self, arg_dict=None, buffer=False):
        """Not implemented.

        :param arg_dict: Query parameters to fill in query (e.g. `:id` with value 387)
        :type arg_dict: optional dict
        :param buffer: Currently not implemented
        :type buffer: optional bool

        :raises NotImplementedError:

        :return: Nothing, always raises NotImplementedError
        """
        raise NotImplementedError(
            "ImpalaDataSource currently does not not support raw format/blobs. "
            'Use method "get_dataframe" for dataframes'
        )






