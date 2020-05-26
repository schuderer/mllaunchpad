# Stdlib imports
from typing import Dict, Generator, Optional, Union

# Third-party imports
import pandas as pd

# Project imports
from mllaunchpad.resource import DataSink, DataSource, Raw


class MockDataSource(DataSource):
    serves = ["food"]

    def get_dataframe(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Union[pd.DataFrame, Generator]:
        pass

    def get_raw(
        self, params: Dict = None, chunksize: Optional[int] = None
    ) -> Raw:
        pass


class MockDataSink(DataSink):
    serves = ["food"]

    def put_dataframe(
        self,
        dataframe: pd.DataFrame,
        params: Dict = None,
        chunksize: Optional[int] = None,
    ) -> None:
        pass

    def put_raw(
        self,
        raw_data: Raw,
        params: Dict = None,
        chunksize: Optional[int] = None,
    ) -> None:
        pass
