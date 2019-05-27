from flask import Flask, request  # import gunicorn  # WSGI - usable for prod, maybe use with nginx
from flask_restful import Resource, Api  # TODO: install watchdog for flask to use (no polling = fewer cpu cycles)
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

    def __init__(self, conf):
        """When initializing ModelApi, your model will be automatically
        retrieved from the model store based on the currently active
        configuration.

        Params:
            conf:   configuration dictionary to use
        """
        self.config = conf
        self.model_config = self.config['model']

        self.model_store = resource.ModelStore(self.config)

        self.datasources = self.init_datasources()

        self.model = self.load_model()

        self.app = Flask(__name__)

    def init_datasources(self):
        logger.info('Initializing datasources...')
        ds = resource.create_data_sources(self.config, tags='predict')
        logger.info('%s datasource(s) initialized: %s', len(ds), list(ds.keys()))

        return ds

    def load_model(self):
        logger.info('Loading model...')
        model, meta = self.model_store.load_trained_model(self.model_config)
        logger.info('Model loaded: {}, version: {}, created {}'.format(meta['name'], meta['version'], meta['created']))

        return model

    def predict_using_model(self, args_dict):
        logger.debug('Prediction input %s', dict(args_dict))
        logger.info('Starting prediction')
        output = self.model.predict(self.model_config, self.datasources, args_dict)
        logger.debug('Prediction output %s', output)
        return output

    def _get_major_version(self):
        match = re.match(r'\d+', self.config['api']['version'])
        if match is None:
            raise ValueError('API version in configuration is malformed.')
        return 'v{}'.format(match.group(0))

    def run(self):
        logger.info('Starting Flask server')

        api = Api(self.app)

        api_name = self.config['api']['resource_name']
        api_version = self._get_major_version()
        api_url = '/{}/{}'.format(api_name, api_version)

        api.add_resource(FlaskPredictionResource,
                         api_url,
                         resource_class_kwargs={'model_api_obj': self})

        self.app.run(debug=True)

        logger.info('Flask server stopped')
