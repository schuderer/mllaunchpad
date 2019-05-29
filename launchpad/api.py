# from flask import Flask
from flask import request
from flask_restful import Resource, Api
import re
from . import resource
import logging

logger = logging.getLogger(__name__)


class FlaskPredictionResource(Resource):
    # Adapted from https://flask-restful.readthedocs.io/en/latest/quickstart.html
    def __init__(self, model_api_obj):
        self.model_api = model_api_obj

    def get(self):  # todo: optional resource identifier like kltid?
        args = request.args
        logger.debug('Received GET request with arguments: %s', args)
        return self.model_api.predict_using_model(args)


class ModelApi:
    """Class to plug a Data-Scientist-created model into.

    This class handles the heavy lifting of APIs for the model.

    The model is a delegate which inherits from (=implements) ModelInterface.
    It needs to provide certain functionality:
       - a predict function

    For details, see the doc-comments in the module modelinterface
    """

    def __init__(self, config, application):
        """When initializing ModelApi, your model will be automatically
        retrieved from the model store based on the currently active
        configuration.

        Params:
            config:       configuration dictionary to use
            application:  flask application to use
        """
        self.model_config = config['model']
        model_store = resource.ModelStore(config)
        self.model = self._load_model(model_store, self.model_config)
        self.datasources = self._init_datasources(config)

        logger.debug('Initializing RESTful API')
        api = Api(application)

        api_name = config['api']['resource_name']
        api_version = self._get_major_version(config)
        api_url = '/{}/{}'.format(api_name, api_version)

        api.add_resource(FlaskPredictionResource,
                         api_url,
                         resource_class_kwargs={'model_api_obj': self})

    def predict_using_model(self, args_dict):
        logger.debug('Prediction input %s', dict(args_dict))
        logger.info('Starting prediction')
        output = self.model.predict(self.model_config, self.datasources, args_dict)
        logger.debug('Prediction output %s', output)
        return output

    @staticmethod
    def _init_datasources(config):
        logger.info('Initializing datasources...')
        ds = resource.create_data_sources(config, tags='predict')
        logger.info('%s datasource(s) initialized: %s', len(ds), list(ds.keys()))

        return ds

    @staticmethod
    def _load_model(model_store, model_config):
        logger.info('Loading model...')
        model, meta = model_store.load_trained_model(model_config)
        logger.info('Model loaded: {}, version: {}, created {}'
                    .format(meta['name'], meta['version'], meta['created']))

        return model

    @staticmethod
    def _get_major_version(config):
        match = re.match(r'\d+', config['api']['version'])
        if match is None:
            raise ValueError('API version in configuration is malformed.')
        return 'v{}'.format(match.group(0))
