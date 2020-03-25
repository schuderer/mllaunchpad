import pandas as pd
from mllaunchpad.resource import DataSource
import logging
from impala.dbapi import connect

logger = logging.getLogger(__name__)


class ImpalaDataSource(DataSource):
    """DataSource for fetching data from Impala tables
    """
    serves = ['dbms.impala']

    def __init__(self, identifier, datasink_config, dbms_config):
        super().__init__(identifier, datasink_config)

        self.dbms_config = dbms_config

        logger.info(
            "Establishing Oracle database connection for datasource {}...".format(
                self.id
            )
        )

    def get_dataframe(self, arg_dict=None, buffer=False):
        """Get the ImpalaDataSource's data as pandas dataframe.
              Configure the DataSource's options dict to pass keyword arguments to impala's connection string.

        Params:
            argsDict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            DataFrame object, possibly cached according to expires-config
        """
        if buffer:
            raise NotImplementedError('Buffered reading not supported yet')

        cached = self._try_get_cached_df()
        if cached is not None:
            return cached

        kw_options = self.options

        # Fetch query
        query = self.config["query"]
        params = arg_dict or {}
        logger.debug(
            "Fetching query {} with params {} and options {}...".format(
                query, params, kw_options
            )
        )

        # Open connection
        conn_args = {k: v for k, v in self.dbms_config.items() if k not in ["type", "options"]}
        conn = connect(**conn_args)

        df = pd.read_sql(
            query, con=conn, params=params, **kw_options
        )

        # Close connection
        conn.close()
        self._cache_df_if_required(df)

        return df

    def get_raw(self, arg_dict=None, buffer=False):
        """Not implemented.

        Params:
            argsDict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            Nothing, throws NotImplementedError
        """
        raise NotImplementedError('Raw bogus not supported yet')






