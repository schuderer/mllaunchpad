import pandas as pd
from mllaunchpad.resource import DataSource
import logging

logger = logging.getLogger(__name__)


class BogusDataSource(DataSource):
    """DataSource for creating nonsense
    """
    serves = ['bogus']

    # def __init__(self, identifier, datasource_config):
    #     super().__init__(identifier, datasource_config)

    def get_dataframe(self, arg_dict=None, buffer=False):
        """Get some pandas dataframe.

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

        return pd.DataFrame({'a': [3,4,5], 'b':[6,7,8]})


    def get_raw(self, arg_dict=None, buffer=False):
        """Not implemented.

        Params:
            argsDict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            Nothing, throws NotImplementedError
        """
        raise NotImplementedError('Raw bogus not supported yet')
