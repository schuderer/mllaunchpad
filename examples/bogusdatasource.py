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
