# from flask import Flask
from flask_restful import Resource, Api, reqparse
import ramlfications
import re
from . import resource
import logging

logger = logging.getLogger(__name__)


def _get_major_api_version(config):
    match = re.match(r'\d+', config['api']['version'])
    if match is None:
        raise ValueError('API version in configuration is malformed.')
    return 'v{}'.format(match.group(0))


def _load_raml(config):
    api_config = config['api']
    raml_file = api_config['raml']
    logger.debug("Reading RAML file %s", raml_file)
    raml = ramlfications.parse(api_config['raml'])

    conf_version = _get_major_api_version(config)
    if raml.version != conf_version:
        raise ValueError('API version in RAML {} does not match API version in config {}'
                         .format(raml.version, conf_version))

    return raml


_type_lookup = {
    'number': float,
    'integer': int,
    'string': str,
    'enum': str  # TODO: enum and other types...
    }


def _request_parser_from_raml(config):
    """We only use query_params and form_params for now (no custom headers, body, etc.).
    Note that they are used interchangeably in code (so even if RAML requires
    only form_params, in reality we also accept the same params as query_params).
    TODO: extend foor lookup-ids (uri_params, e.g. clientquestions/{clientid})
    """
    raml = _load_raml(config)

    api_config = config['api']

    name = '/' + api_config['resource_name']
    # only dealing with "get" method resources for now
    resources = [r for r in raml.resources if r.name == name and r.method == 'get']
    if len(resources) != 1:
        raise ValueError(('RAML must contain exactly resource with name "{}" and '
                         + 'method="get". There are {} matching ones. Resources in RAML: {}')
                         .format(name, len(resources), raml.resources))

    allParams = (resources[0].query_params or []) + (resources[0].form_params or [])
    addedArguments = set()
    parser = reqparse.RequestParser(bundle_errors=True)
    for p in allParams:
        if p.name in addedArguments and not p.repeat:
            raise ValueError('Cannot handle RAML multiple parameters with same name %s',
                             p.name)

        parser.add_argument(p.name,
                            type=_type_lookup[p.type],
                            required=p.required,
                            action='append' if p.repeat else 'store',
                            help=str(p.description))
        addedArguments.add(p.name)

    return parser


class FlaskPredictionResource(Resource):
    # Adapted from https://flask-restful.readthedocs.io/en/latest/quickstart.html

    def __init__(self, model_api_obj, parser):
        self.model_api = model_api_obj
        self.parser = parser
        # todo (optional): marshal output?

    def get(self):  # todo: optional resource identifier like kltid?
        args = self.parser.parse_args()  # treats query_params and form_params as interchangable
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
        api_version = _get_major_api_version(config)
        api_url = '/{}/{}'.format(api_name, api_version)

        parser = _request_parser_from_raml(config)
        api.add_resource(FlaskPredictionResource,
                         api_url,
                         resource_class_kwargs={'model_api_obj': self,
                                                'parser': parser})

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
