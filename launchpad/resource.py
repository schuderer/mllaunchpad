import glob
import os
import shutil
import dill as pickle
import json
from datetime import datetime
import getpass
import pandas as pd
from time import time
import logging

logger = logging.getLogger(__name__)

SUPPORTED_FILE_TYPES = ['csv', 'csv2', 'rawfile']
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_FILES = "%Y-%m-%d_%H-%M-%S"


class ModelStore():
    """Deals with persisting, loading, updating metrics metadata of models.
    Abstracts away how and where the model is kept.

    TODO: Smarter querying like "get me the model with the currently (next)
    best metrics which serves a particular API resource."
    """

    def __init__(self, config):
        """Get a model store based on the config settings

        Params:
            config: configuration dict
        """
        self.location = config['model_store']['location']
        if not os.path.exists(self.location):
            os.makedirs(self.location)


    def _get_model_base_name(self, model_conf):
        return os.path.join(self.location, "{}_{}".format(model_conf['name'], model_conf['version']))


    def _load_metadata(self, base_name):
        metadata_name = base_name + ".json"
        with open(metadata_name, 'r') as f:
            meta = json.load(f)

        return meta


    def _dump_metadata(self, base_name, metadata):
        metadata_name = base_name + ".json"
        with open(metadata_name, 'w') as f:
            json.dump(metadata, f)


    def _backup_old_model(self, base_name):
        backup_dir = os.path.join(self.location, "previous")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        infix = datetime.now().strftime(DATE_FORMAT_FILES)
        for file in glob.glob(base_name + "*"):
            fn_ext = os.path.basename(file)
            fn, ext = os.path.splitext(fn_ext)
            new_file_name = "{}_{}{}".format(fn, infix, ext)
            logger.debug("Backing up previous model file {} as {}".format(fn_ext, new_file_name))
            shutil.copy(file, os.path.join(backup_dir, new_file_name))


    def dump_trained_model(self, complete_conf, model, metrics):
        """Save a model object in the model store. Some metadata will also
        be saved along the model, including the metrics which is the second parameter.

        Params:
            model_conf:  the config dict of our model
            model:       the model object to store
            metrics:     metrics dictionary

        Returns:
            Nothing
        """
        model_conf = complete_conf['model']
        base_name = self._get_model_base_name(model_conf)

        # Check if exists and backup if it does
        self._backup_old_model(base_name)

        # Save model itself
        pkl_name = base_name + ".pkl"
        with open(pkl_name, 'wb') as f:
            pickle.dump(model, f)

        # Save metadata
        api_conf = complete_conf['api']
        meta = {
            'name': model_conf['name'],
            'version': model_conf['version'],
            'api_name': api_conf['resource_name'],
            'api_version': api_conf['version'],
            'created': datetime.now().strftime(DATE_FORMAT),
            'created_by': getpass.getuser(),
            'metrics': metrics,
            'metrics_history': {datetime.now().strftime(DATE_FORMAT): metrics},
            'config_snapshot': model_conf
        }
        self._dump_metadata(base_name, meta)


    def load_trained_model(self, model_conf):
        """Load a model object from the model store. Some metadata will also
        be loaded along the model.

        Params:
            model_conf:  the config dict of our model

        Returns:
            Tuple of model object and metadata dictionary
        """
        base_name = self._get_model_base_name(model_conf)

        pkl_name = base_name + ".pkl"
        with open(pkl_name, 'rb') as f:
            model = pickle.load(f)

        meta = self._load_metadata(base_name)

        return model, meta


    def update_model_metrics(self, model_conf, metrics):
        """Update the test metrics for a previously stored model
        """
        base_name = self._get_model_base_name(model_conf)
        meta = self._load_metadata(base_name)
        meta['metrics'] = metrics
        meta['metrics_history'][datetime.now().strftime(DATE_FORMAT)] = metrics
        self._dump_metadata(base_name, meta)



def create_data_sources(config, tag=None):
    """Creates the data sources as defined in the configuration dict.
    Filters them by tag.

    Params:
        config: configuration dictionary
        tag:    optionally filter for only matching datasources

    Returns:
        dict with keys=datasource names, values=instantiated DataSource objects
    """

    ds_objects = {}

    if 'datasources' not in config or type(config['datasources']) is not dict:
        logger.info("No datasources defined in configuration")
        return ds_objects

    datasources = config['datasources']
    for id in datasources:
        ds_config = datasources[id]
        if tag is not None and \
            ('tags' not in ds_config
             or tag != ds_config['tags']
                and tag not in ds_config['tags']):
            continue
        ds_type = ds_config['type']

        logger.debug("Initializing datasource %s of type %s...", id, ds_type)
        if ds_type in SUPPORTED_FILE_TYPES:
            ds_objects[id] = FileDataSource(id, ds_config)
        elif ds_type == 'dbms':
            dbms_id = ds_config['dbms']
            dbms = config['dbms'][dbms_id]
            dbms_type = dbms['type']
            if dbms_type == 'oracle':
                ds_objects[id] = OracleDataSource(id, ds_config, dbms)
            elif dbms_type == 'hive':
                raise NotImplementedError("Sorry, still have to implement this one.")
            else:
                raise ValueError("Unsupported dbms type: {}".format(dbms_type))
        else:
            raise ValueError("Unsupported datasource type: {}".format(ds_type))
        logger.debug("Datasource %s initialized", id)

    return ds_objects


# TODO: will possibly also need DataSinks...
class DataSource():
    """Interface, used by the Data Scientist's model to get its data from.
    Concrete DataSources (for files, data bases, etc.) need to inherit from this class.
    """

    def __init__(self, identifier, datasource_config):
        """Please call super().__init(...) when overwriting this method
        """
        self.id = identifier
        self.config = datasource_config
        self.options = self.config['options'] if 'options' in self.config else {}

        self.expires = self.config['expires'] if 'expires' in self.config else 0

        self._cached_df = None
        self._cached_df_time = 0
        self._cached_raw = None
        self._cached_raw_time = 0

    def get_dataframe(self, argDict={}, buffer=False):
        ...

    def get_raw(self, argDict={}, buffer=False):
        ...

    def try_get_cached_df(self):
        if self._cached_df is not None \
           and (self.expires == -1  # cache indefinitely
                or (self.expires > 0
                    and time() <= self._cached_df_time + self.expires)):
            logger.debug("Returning cached dataframe")
            return self._cached_df
        else:  # either immediately expires (0) or has expired in meantime (>0)
            return None

    def try_get_cached_raw(self):
        if self._cached_raw is not None \
           and (self.expires == -1  # cache indefinitely
                or (self.expires > 0
                    and time() <= self._cached_raw_time + self.expires)):
            logger.debug("Returning cached raw data")
            return self._cached_raw
        else:  # either immediately expires (0) or has expired in meantime (>0)
            return None

    def cache_df_if_required(self, df):
        if self.expires != 0:
            self._cached_df_time = time()
            self._cached_df = df

    def cache_raw_if_required(self, raw):
        if self.expires != 0:
            self._cached_raw_time = time()
            self._cached_raw = raw

    def __del__(self):
        """Overwrite to clean up any resources (connections, temp files, etc.).
        """
        ...


class DbmsDataSource(DataSource):
    """DataSource for database connections
    """

    def __init__(self, identifier, datasource_config, dbms_config):
        super().__init__(identifier, datasource_config)

        self.dbms_config = dbms_config


class OracleDataSource(DbmsDataSource):
    """DataSource for database connections
    """

    def __init__(self, identifier, datasource_config, dbms_config):
        super().__init__(identifier, datasource_config, dbms_config)

        import cx_Oracle  # TODO: check whether importing here actually saves space/time

        logger.info("Establishing Oracle database connection for datasource {}...".format(self.id))

        user = self.dbms_config['username']
        pw = self.dbms_config['password']
        dsn_tns = cx_Oracle.makedsn(
            self.dbms_config['host'],
            self.dbms_config['port'],
            service_name=self.dbms_config['service_name']
        )
        logger.debug("Oracle connection string: {}".format(dsn_tns))

        kwOptions = self.dbms_config['options'] if 'options' in self.dbms_config else {}
        self.connection = cx_Oracle.connect(user, pw, dsn_tns, **kwOptions)


    def get_dataframe(self, argDict={}, buffer=False):
        if buffer:
            raise NotImplementedError("Buffered reading not supported yet")

        cached = self.try_get_cached_df()
        if cached is not None:
            return cached

        # TODO: maybe want to open/close connection on every method call (shouldn't happen often)
        query = self.config['query']
        params = argDict
        kwOptions = self.options

        logger.debug("Fetching query {} with params {} and options {}...".format(query, params, kwOptions))
        df = pd.read_sql(query, con=self.connection, params=params, **kwOptions)

        self.cache_df_if_required(df)

        return df


    def get_raw(self, argDict={}, buffer=False):
        raise TypeError("Oracle Databases are not available in raw format")


    def __del__(self):
        if hasattr(self, 'connection'):
            self.connection.close()



class FileDataSource(DataSource):
    """DataSource for fetching data from files
    """

    def __init__(self, identifier, datasource_config):
        super().__init__(identifier, datasource_config)

        type = datasource_config['type']
        if type not in SUPPORTED_FILE_TYPES:
            raise ValueError("'{}' is not a datasource file type (in datasource '{}').".format(type, identifier))

        self.type = type
        self.path = datasource_config['path']


    def get_dataframe(self, argDict={}, buffer=False):
        if buffer:
            raise NotImplementedError("Buffered reading not supported yet")

        cached = self.try_get_cached_df()
        if cached is not None:
            return cached

        kwOptions = self.options

        logger.debug("Loading type {} file {} with options {}...".format(self.type, self.path, kwOptions))
        if self.type == 'csv':
            df = pd.read_csv(self.path, **kwOptions)
        elif self.type == 'csv2':
            df = pd.read_csv(self.path, sep=";", decimal=",", **kwOptions)
        else:
            raise ValueError("Cannot read raw file as a data frame. Use method 'get_raw' instead")

        self.cache_df_if_required(df)

        return df


    def get_raw(self, argDict={}, buffer=False):
        if buffer:
            raise NotImplementedError("Buffered reading not supported yet")

        cached = self.try_get_cached_raw()
        if cached is not None:
            return cached

        kwOptions = self.options

        logger.debug("Loading raw binary file {} with options {}...".format(self.type, self.path, kwOptions))
        with open(self.path, 'rb') as bin_file:
            raw = bin_file.read(**kwOptions)

        self.cache_raw_if_required(raw)

        return raw
