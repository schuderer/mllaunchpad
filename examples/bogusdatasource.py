import logging

from mllaunchpad.resource import DataSource
import pandas as pd


logger = logging.getLogger(__name__)


class BogusDataSource(DataSource):
    """DataSource for creating nonsense
    """

    serves = ["bogus"]

    # def __init__(self, identifier, datasource_config):
    #     super().__init__(identifier, datasource_config)

    def get_dataframe(self, params=None, chunksize=None):
        """Get some pandas dataframe.

        Params:
            argsDict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            DataFrame object, possibly cached according to expires-config
        """
        if chunksize:
            raise NotImplementedError("Buffered reading not supported yet")

        kw_options = self.options

        return pd.DataFrame({"a": [3, 4, 5], "b": [6, 7, 8]}, **kw_options)

    def get_raw(self, params=None, chunksize=None):
        """Not implemented.

        Params:
            argsDict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            Nothing, throws NotImplementedError
        """
        raise NotImplementedError("Raw bogus not supported yet")

    # csv reader test
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
            "Loading type {} file {} with chunksize {} and options {}...".format(
                self.type, self.path, chunksize, kw_options
            )
        )
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
        input_dtypes = pd.read_csv('~/Documents/Coding/csvtest/test.dtypes', header=0).set_index('Columnname')
        dts = {item: input_dtypes.loc[item]['Types'] for item in input_dtypes.index if
               input_dtypes.loc[item]['Types'] != 'datetime'}
        date_list = [item for item in input_dtypes.index if input_dtypes.loc[item]['Types'] == 'datetime']
        test = pd.read_csv('~/Documents/Coding/csvtest/test.csv', dtype=dts, parse_dates=date_list, header=0)

        return df
