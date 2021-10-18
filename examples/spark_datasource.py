import logging
# import os
from typing import Dict, Optional, Union, Generator  # , Iterable, Optional, Union, cast

from mllaunchpad.resource import DataSource, Raw
from mllaunchpad.datasources import fill_nas, get_connection_args
# import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
# from pyspark.sql.types import *
from sqlalchemy.dialects import mysql
from sqlalchemy import text

logger = logging.getLogger(__name__)


def bind_sql_params(query, params):
    """Bind SQL params in a way as to avoid SQL injection.
    This is needed because SparkSession.sql does not allow parameters.
    """
    bound_query = str(
        text(query)
            .bindparams(**params)
            .compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
    return bound_query


class SparkDataSource(DataSource):
    """DataSource to retrieve Spark data as Spark DataFrames or Pandas DataFrames.

    Configuration example::

        plugins:
          - examples.spark_datasource  # or wherever you put this module

        dbms:
          # ... (other connections)
          # Example:
          my_connection:  # NOTE: You can use the same connection for several datasources and datasinks
            type: spark
            master: local[*]
            options:
              # dict, passed to `config()` when creating the spark session
              spark.hadoop.yarn.resourcemanager.principal_var: HADOOP_USER_NAME

        # ...
        datasources:
          # ... (other datasources)
          my_datasource:
            type: dbms.my_connection
            query: SELECT * FROM somewhere.my_table WHERE id = :id  # fill `:params` by calling `get_dataframe` with a `dict`
            expires: 0    # generic parameter, see documentation on DataSources
            tags: [train] # generic parameter, see documentation on DataSources and DataSinks
    """

    serves = ["dbms.spark"]

    def __init__(
        self, identifier: str, datasource_config: Dict, dbms_config: Dict
    ):
        super().__init__(identifier, datasource_config)

        self.dbms_config = dbms_config

        logger.info("Creating spark session for datasource {}...".format(self.id))
        spark_prep = (SparkSession
                      .builder
                      .appName("SparkDataSource_" + self.id)
                      .master(self.dbms_config["master"])
                      )

        spark_cfg = get_connection_args(self.dbms_config)
        for key, val in spark_cfg.items():
            spark_prep = spark_prep.config(key, val)
        self.spark = spark_prep.getOrCreate()

    def get_dataframe(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Union[pd.DataFrame, Generator]:
        """Get data as pandas dataframe.

        Null values are replaced by ``numpy.nan``.

        Example::

            my_df = data_sources["my_datasource"].get_dataframe({"id": 387})

        :param params: Query parameters to fill in query (e.g. replace query's `:id` parameter with value `387`)
        :type params: optional dict
        :param chunksize: Return an iterator where chunksize is the number of rows to include in each chunk.
        :type chunksize: not supported

        :return: DataFrame object, possibly cached according to config value of `expires:`
        """
        df = self.get_spark_dataframe(params, chunksize).toPandas()
        return fill_nas(df, as_generator=chunksize is not None)

    def get_spark_dataframe(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Union[pd.DataFrame, Generator]:
        """Get data as Spark dataframe.

        Example::

            spark_df = data_sources["my_datasource"].get_spark_dataframe({"id": 387})

        :param params: Query parameters to fill in query (e.g. replace query's `:id` parameter with value `387`)
        :type params: optional dict
        :param chunksize: Return an iterator where chunksize is the number of rows to include in each chunk.
        :type chunksize: not supported

        :return: Spark DataFrame object, possibly cached according to config value of `expires:`
        """
        if chunksize:
            raise ValueError("Parameter `chunksize` not supported for SparkDataSource.")

        raw_query = self.config["query"]
        params = params or {}
        query = bind_sql_params(raw_query, params)
        kw_options = self.options

        logger.debug(
            "Fetching query {} with params {}, chunksize {}, and options {}...".format(
                query, params, chunksize, kw_options
            )
        )
        return self.spark.sql(query)

    def get_raw(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Raw:
        """Not implemented.

        :raises NotImplementedError: Raw/blob format currently not supported.
        """
        raise NotImplementedError(
            "SparkDataSource currently does not not support raw format/blobs. "
            'Use method "get_dataframe" for dataframes'
        )


def test():
    from mllaunchpad import get_validated_config_str
    test_cfg = get_validated_config_str("""
    dbms:
      # ... (other connections)
      # Example:
      my_connection:  # NOTE: You can use the same connection for several datasources and datasinks
        type: spark
        master: local[*]
        options:
          # dict, passed to `config()` when creating the spark session
          spark.hadoop.yarn.resourcemanager.principal_var: HADOOP_USER_NAME
    # ...
    datasources:
      # ... (other datasources)
      my_datasource:
        type: dbms.my_connection
        query: SELECT * FROM cml_poc.iris
        #WHERE seniorcitizen = :senior  # fill `:params` by calling `get_dataframe` with a `dict`
        expires: 0    # generic parameter, see documentation on DataSources
        tags: [train] # generic parameter, see documentation on DataSources and DataSinks
    model:
      name: bla
      version: 1.0.0
      module: bla
    model_store:
      location: bla
  """)
    ds = SparkDataSource("my_datasource", test_cfg["datasources"]["my_datasource"], test_cfg["dbms"]["my_connection"])
    try:
        df = ds.get_dataframe()
        # df = ds.get_spark_dataframe().toPandas()
    finally:
        ds.spark.stop()
    return df
