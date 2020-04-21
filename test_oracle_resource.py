# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 22:19:33 2020

@author: xg16129
"""

# Stdlib imports
import os
os.chdir('C:/Users/xg16129/mllaunchpad')

# Third-party imports
import pytest
import pandas as pd
import cx_Oracle

# Project imports
from mllaunchpad.resource import OracleDataSource



options = None
options = {} if options is None else options
cfg = {
    "type": "dbms.my_connection",
    "query": "blabla",
    "tags": ["train"],
    "options": options,
}
dbms_cfg = {
    "type": "oracle",
    "host": "host.example.com",
    "port": 1251,
    "user_var": "MY_USER_ENV_VAR",
    "password_var": "MY_PW_ENV_VAR",
    "service_name": "servicename.example.com",
    "options": options,
}


def test_regression_oracle_nas_issue86():
    """The initialization of an Adder object should not error"""
    
    _ = OracleDataSource("bla", cfg, dbms_cfg)
    



