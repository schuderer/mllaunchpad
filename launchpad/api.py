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
        raise ValueError('API version in configuration is malformed. Expected x.y.z, got {}'
                         .format(config['api']['version']))
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
    'boolean': bool
    # RAML Types: any, object, array, union via type expression,
    #             one of the following scalar types: number, boolean, string,
    #             date-only, time-only, datetime-only, datetime, file, integer, or nil
    }


def _create_request_parser(resource_obj):
    """We only use query_params and form_params for now (no custom headers, body, etc.).
    Note that they are used interchangeably in code (so e.g. even if RAML requires
    only form_params, in reality we also accept the same params as query_params).
    """
    all_params = (resource_obj.query_params or []) + (resource_obj.form_params or [])
    added_arguments = set()
    parser = reqparse.RequestParser(bundle_errors=True)
    for p in all_params:
        if p.name in added_arguments and not p.repeat:
            raise ValueError('Cannot handle RAML multiple parameters with same name {}'
                             .format(p.name))

        parser.add_argument(p.name,
                            type=_type_lookup[p.type],
                            required=p.required,
                            default=p.default,
                            action='append' if p.repeat else 'store',
                            choices=p.enum,
                            help=str(p.description)+' - Error: {error_msg}')
        added_arguments.add(p.name)

    if resource_obj.uri_params and resource_obj.uri_params[-1].name in added_arguments:
        raise ValueError('Resource URI parameter in RAML "{}" must not have same name as a parameter'
                         .format(resource_obj.uri_params[-1].name))

    return parser


def _get_resources(raml):
    """Gets relevant resources from RAML
    """
    # only dealing with "get" method resources for now
    usable_methods = ['get']
    usable_rs = [r for r in raml.resources if r.method in usable_methods]  # r.path == name and
    rs_without_resource_id = [r for r in usable_rs if not r.uri_params]
    rs_with_resource_id = [r for r in usable_rs if r.uri_params]
    if len(usable_rs) == 0 or len(usable_rs) > 2 or\
       len(rs_without_resource_id) > 1 or len(rs_with_resource_id) > 1:
        raise ValueError(('RAML must contain one or two resources with a method of "{}". '
                         + 'At most one resource each with and without uri parameter (resource id)'
                         + 'There are {} resources with matching methods. Resources in RAML: {}')
                         .format(usable_methods, len(usable_rs), raml.resources))

    res_normal = rs_without_resource_id[0] if rs_without_resource_id else None
    res_with_id = rs_with_resource_id[0] if rs_with_resource_id else None

    return res_normal, res_with_id


class QueryResource(Resource):
    # Adapted from https://flask-restful.readthedocs.io/en/latest/quickstart.html

    def __init__(self, model_api_obj, parser):
        self.model_api = model_api_obj
        self.parser = parser

    def get(self):
        args = self.parser.parse_args(strict=True)  # treats query_params and form_params as interchangeable
        logger.debug('Received GET request with arguments: %s', args)
        return self.model_api.predict_using_model(args)


class GetByIdResource(Resource):
    def __init__(self, model_api_obj, parser, id_name):
        self.model_api = model_api_obj
        self.parser = parser
        self.id_name = id_name

    def get(self, some_resource_id):
        args = self.parser.parse_args(strict=True)  # treats query_params and form_params as interchangeable
        args[self.id_name] = some_resource_id
        logger.debug('Received GET request for %s %s with arguments: %s',
                     self.id_name, some_resource_id, args)
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
        self.datasources, self.datasinks = self._init_datasources(config)

        logger.debug('Initializing RESTful API')
        api = Api(application)

        api_name = config['api']['name']
        api_version = _get_major_api_version(config)
        api_url = '/{}/{}'.format(api_name, api_version)

        raml = _load_raml(config)
        res_normal, res_with_id = _get_resources(raml)

        if res_normal:
            logger.debug('Adding resource %s to api %s', res_normal.path, api_url)
            resource_url = api_url + res_normal.path
            normal_parser = _create_request_parser(res_normal)
            api.add_resource(QueryResource,
                             resource_url,
                             resource_class_kwargs={'model_api_obj': self,
                                                    'parser': normal_parser})

        if res_with_id:
            logger.debug('Adding resource %s to api %s', res_with_id.path, api_url)
            uri_param_name = res_with_id.uri_params[-1].name
            resource_url = api_url + res_with_id.parent.path + '/<string:some_resource_id>'
            with_id_parser = _create_request_parser(res_with_id)
            api.add_resource(GetByIdResource,
                             resource_url,
                             resource_class_kwargs={'model_api_obj': self,
                                                    'parser': with_id_parser,
                                                    'id_name': uri_param_name})

    def predict_using_model(self, args_dict):
        logger.debug('Prediction input %s', dict(args_dict))
        logger.info('Starting prediction')
        output = self.model.predict(self.model_config, self.datasources, self.datasinks, args_dict)
        logger.debug('Prediction output %s', output)
        return output

    @staticmethod
    def _init_datasources(config):
        logger.info('Initializing datasources...')
        dso, dsi = resource.create_data_sources_and_sinks(config, tags='predict')
        logger.info('%s datasource(s) initialized: %s', len(dso), list(dso.keys()))
        logger.info('%s datasink(s) initialized: %s', len(dsi), list(dsi.keys()))

        return dso, dsi

    @staticmethod
    def _load_model(model_store, model_config):
        logger.info('Loading model...')
        model, meta = model_store.load_trained_model(model_config)
        logger.info('Model loaded: {}, version: {}, created {}'
                    .format(meta['name'], meta['version'], meta['created']))

        return model
