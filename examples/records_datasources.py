import logging

import records

from mllaunchpad.resource import DataSource
from mllaunchpad.resource import get_user_pw

logger = logging.getLogger(__name__)


class RecordsDbDataSource(DataSource):
    """DataSource for a bunch of relational database types:
    RedShift, Postgres, MySQL, SQLite, Oracle, Microsoft SQL
    """
    serves = ['dbms.oracle', 'dbms.redshift', 'dbms.postgres', 'dbms.mysql', 'dbms.sqlite', 'dbms.ms_sql']

    def __init__(self, identifier, datasource_config, dbms_config):
        super().__init__(identifier, datasource_config)

        self.dbms_config = dbms_config

        logger.info(
            "Establishing Records database connection for datasource {}...".format(self.id)
        )
        # if "connect" not in dbms_config:
        #     raise ValueError(f'No connection string (property "connect") in datasource {self.id} config')
        dbtype = dbms_config['type']
        user, pw = get_user_pw(dbms_config)
        host = dbms_config['host']
        port = ":" + str(dbms_config['port']) if 'port' in dbms_config else ''
        service_name = "/?service_name=" + dbms_config['service_name'] if 'service_name' in dbms_config else ''
        connection_string = f"{dbtype}://{user}:{pw}@{host}{port}{service_name}"
        self.db = records.Database(connection_string)

    def get_dataframe(self, arg_dict=None, buffer=False):
        """Get datasource as a pandas dataframe.

        Params:
            args_dict: optional query parameters
            buffer: optional, currently not implemented

        Returns:
            DataFrame object, possibly cached according to expires-config
        """
        if buffer:
            raise NotImplementedError('Buffered reading not supported yet')
            # the resulting `rows` of a query provides a nice way to do this, though

        cached = self._try_get_cached_df()
        if cached is not None:
            return cached

        query = self.config["query"]
        params = arg_dict or {}
        kw_options = self.options or {}

        logger.debug(
            "Fetching query {} with params {} and options {}...".format(
                query, params, kw_options
            )
        )
        rows = self.db.query(query, fetchall=True, **params)
        df = rows.export('df')

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
        raise NotImplementedError('Raw data not supported')

    # def __del__(self):
    #     if hasattr(self, "db"):
    #         self.db.close()
