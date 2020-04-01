import logging

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

    Note: In order to access a kerberized cluster, you need the correct packages.
    We found the following packages to work reliably::

        $ pip install pykerberos thrift_sasl impyla pandas
        (for Windows, use winkerberos instead of pykerberos)
    """
    serves = ['dbms.impala']

    def __init__(self, identifier, datasink_config, dbms_config):
        super().__init__(identifier, datasink_config)

        self.dbms_config = dbms_config

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
        conn = connect(**conn_args)

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

        # Close connection
        conn.close()
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
        raise NotImplementedError('Raw data not supported.')






