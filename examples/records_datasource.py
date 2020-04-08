import logging
from typing import Dict, Optional

from mllaunchpad.resource import DataSource, get_user_pw


logger = logging.getLogger(__name__)

try:
    import records
except ModuleNotFoundError:
    logger.warning("Please install the Records package to be able to use RecordsDbDataSource.")


class RecordsDbDataSource(DataSource):
    """DataSource for a bunch of relational database types:
    RedShift, Postgres, MySQL, SQLite, Oracle, Microsoft SQL.

    EXPERIMENTAL

    See :attr:`serves` for the available types.

    Creates a long-living connection on initialization.

    Configuration::

        dbms:
          # ... (other connections)
          my_connection:  # NOTE: You can use the same connection for several datasources and datasinks
            type: oracle  # see attribute serves for available types
            host: host.example.com
            port: 1251  # optional
            user_var: MY_USER_ENV_VAR
            password_var: MY_PW_ENV_VAR  # optional
            service_name: servicename.example.com  # optional
            options: {}  # used as **kwargs when initializing the DB connection
        # ...
        datasources:
          # ... (other datasources)
          my_datasource:
            type: dbms.my_connection
            query: SELECT * FROM users.my_table where id = :id  # fill `:params` by calling `get_dataframe` with a `dict`
            expires: 0     # generic parameter, see documentation on DataSources
            tags: [train]  # generic parameter, see documentation on DataSources and DataSinks
    """

    serves = [
        "dbms.oracle",
        "dbms.redshift",
        "dbms.postgres",
        "dbms.mysql",
        "dbms.sqlite",
        "dbms.ms_sql",
    ]

    def __init__(self, identifier: str, datasource_config: Dict, dbms_config: Optional[Dict]):
        super().__init__(identifier, datasource_config)

        self.dbms_config = dbms_config

        logger.info(
            "Establishing Records database connection for datasource {}...".format(
                self.id
            )
        )
        # if "connect" not in dbms_config:
        #     raise ValueError(f'No connection string (property "connect") in datasource {self.id} config')
        dbtype = dbms_config["type"]
        user, pw = get_user_pw(dbms_config["user_var"], dbms_config["password_var"])
        host = dbms_config["host"]
        port = ":" + str(dbms_config["port"]) if "port" in dbms_config else ""
        service_name = (
            "/?service_name=" + dbms_config["service_name"]
            if "service_name" in dbms_config
            else ""
        )
        kwargs = dbms_config.get("options", {})
        connection_string = f"{dbtype}://{user}:{pw}@{host}{port}{service_name}"
        self.db = records.Database(connection_string, **kwargs)

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
            raise NotImplementedError("Buffered reading not supported yet")
            # the resulting `rows` of a query provides a nice way to do this, though

        cached = self._try_get_cached_df()
        if cached is not None:
            return cached

        query = self.config["query"]
        params = arg_dict or {}

        logger.debug(
            "Fetching query {} with params {}...".format(
                query, params
            )
        )
        rows = self.db.query(query, fetchall=True, **params)
        df = rows.export("df")

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
        raise NotImplementedError("Raw data not supported")

    # def __del__(self):
    #     if hasattr(self, "db"):
    #         self.db.close()
