import pandas as pd
from mllaunchpad.resource import DataSource
import logging

logger = logging.getLogger(__name__)


class ImapalaDataSource(DataSource):
    """DataSource for creating nonsense
    """
    serves = ['impala']

    def __init__(self, identifier, datasource_config):
        super().__init__(identifier, datasource_config)

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


        # impala code hier
        # open, ophalen, sluiten
        return pd.DataFrame({'a': [3,4,5], 'b':[6,7,8]})

    def get_raw(self, arg_dict=None, buffer=False):
        """Not implemented.

        Params:
            argsDict: optional, currently not implemented
            buffer: optional, currently not implemented

        Returns:
            Nothing, throws NotImplementedError
        """
        raise NotImplementedError('Raw bogus not supported yet') # waarom get_raw?


"""
Alvast heel kort: Het idee is dat het datasource-object met de desbetreffende config geinitieerd wordt waarin bijvoorbeeld een HIVE-query staat.
 eze query is wat opgehaald moet worden als de gebruikerscode de get_dataframe() methode aanroept. 
Het cachen is optioneel (ook via config aangegeven).
 Basisfunctionaliteit is het ophalen van de data die je op dit moment krijgt als je de query draait."""

#import impala
import os
import getpass
from impala.dbapi import connect
conn = connect(host='bda1node04.office01.internalcorp.net', port=8888,kerberos_service_name='hive',auth_mechanism='GSSAPI')

cursor = conn.cursor()
cursor.execute('SELECT * FROM mytable LIMIT 100')
print cursor.description  # prints the result set's schema # impala-shell -i bda1node04 --ssl

results = cursor.fetchall()
#bda1node04.office01.internalcorp.net:8888

#host=os.environ['IP_IMPALA'], port=21050, user=os.environ['USER'], password=os.environ['PASSWORD'], auth_mechanism='PLAIN'

'''
impyla==0.15.0
sasl==0.2.1
thrift_sasl==0.2.1
thriftpy==0.3.9
thriftpy2==0.4.0


sudo apt-get install libsasl2-dev libsasl2-2 libsasl2-modules-gssapi-mit
'''
