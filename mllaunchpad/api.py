# -*- coding: utf-8 -*-

"""This module contains functionality for generic creation
   and handling of RESTful APIs for Machine Learning Models.
   Among others, it handles parsing the RAML definition,
   and validating parameters.
"""

# Stdlib imports
import logging
import re

# Third-party imports
# from flask import Flask
from flask_restful import Api, reqparse, Resource
import ramlfications
import werkzeug

# Application imports
from mllaunchpad import resource

logger = logging.getLogger(__name__)

# TODO: factor out datasource/model preparation code -- use model_actions instead of low-level functionality


def _get_major_api_version(config):
    match = re.match(r"\d+", config["api"]["version"])
    if match is None:
        raise ValueError(
            "API version in configuration is malformed. Expected x.y.z, got {}".format(
                config["api"]["version"]
            )
        )
    return "v{}".format(match.group(0))


def _load_raml(config):
    api_config = config["api"]
    raml_file = api_config["raml"]
    logger.debug("Reading RAML file %s", raml_file)
    raml = ramlfications.parse(api_config["raml"])

    conf_version = _get_major_api_version(config)
    if raml.version != conf_version:
        raise ValueError(
            "API version in RAML {} does not match API version in config {}".format(
                raml.version, conf_version
            )
        )

    return raml


_type_lookup = {
    "number": float,
    "integer": int,
    "string": str,
    "boolean": bool
    # RAML Types: any, object, array, union via type expression,
    #             one of the following scalar types: number, boolean, string,
    #             date-only, time-only, datetime-only, datetime, file, integer, or nil
}


def _create_request_parser(resource_obj):
    """We only use query_params and form_params for now (no custom headers, body, etc.).
    Note that they are used interchangeably in code (so e.g. even if RAML requires
    only form_params, in reality we also accept the same params as query_params).
    """
    all_params = (resource_obj.query_params or []) + (
        resource_obj.form_params or []
    )
    added_arguments = set()
    parser = reqparse.RequestParser(bundle_errors=True)
    for p in all_params:
        if p.name in added_arguments and not p.repeat:
            raise ValueError(
                "Cannot handle RAML with multiple parameters sharing same name {}".format(
                    p.name
                )
            )

        parser.add_argument(
            p.name,
            type=_type_lookup[p.type],
            required=p.required,
            default=p.default,
            action="append" if p.repeat else "store",
            choices=p.enum,
            help=str(p.description) + " - Error: {error_msg}",
        )
        added_arguments.add(p.name)

    if (
        resource_obj.uri_params
        and resource_obj.uri_params[-1].name in added_arguments
    ):
        raise ValueError(
            'Resource URI parameter in RAML "{}" must not have same name as a parameter'.format(
                resource_obj.uri_params[-1].name
            )
        )

    if (
        resource_obj.body
        and resource_obj.body[0].mime_type == "multipart/form-data"
    ):
        # todo: how can we make sure the file mime type is correct?
        parser.add_argument(
            "file", type=werkzeug.FileStorage, location="files"
        )

    return parser


def _get_resources(raml):
    """Gets relevant resources from RAML
    """
    # only dealing with "get" method resources for now
    usable_methods = ["get", "post"]
    usable_rs = [
        r for r in raml.resources if r.method in usable_methods
    ]  # r.path == name and
    rs_without_resource_id = [
        r for r in usable_rs if not r.uri_params and not r.body
    ]
    rs_with_resource_id = [r for r in usable_rs if r.uri_params]
    rs_file_upload = [
        r
        for r in usable_rs
        if r.body and r.body[0].mime_type == "multipart/form-data"
    ]
    if (
        len(usable_rs) == 0
        or len(usable_rs) > 3
        or len(rs_without_resource_id) > 1
        or len(rs_with_resource_id) > 1
        or len(rs_file_upload) > 1
    ):
        raise ValueError(
            (
                "RAML must contain one to three resources with a method of '{}'. "
                "At most one resource each with and without uri parameter (resource id) "
                "or one file upload resource.\n"
                "There are {} resources with matching methods. Resources in RAML: {}"
            ).format(usable_methods, len(usable_rs), raml.resources)
        )

    res_normal = rs_without_resource_id[0] if rs_without_resource_id else None
    res_with_id = rs_with_resource_id[0] if rs_with_resource_id else None
    res_file = rs_file_upload[0] if rs_file_upload else None

    return res_normal, res_with_id, res_file


class QueryResource(Resource):
    # Adapted from https://flask-restful.readthedocs.io/en/latest/quickstart.html

    def __init__(self, model_api_obj, parser):
        self.model_api = model_api_obj
        self.parser = parser

    def get(self):
        args = self.parser.parse_args(
            strict=True
        )  # treats query_params and form_params as interchangeable
        logger.debug("Received GET request with arguments: %s", args)
        return self.model_api.predict_using_model(args)


class GetByIdResource(Resource):
    def __init__(self, model_api_obj, parser, id_name):
        self.model_api = model_api_obj
        self.parser = parser
        self.id_name = id_name

    def get(self, some_resource_id):
        args = self.parser.parse_args(
            strict=True
        )  # treats query_params and form_params as interchangeable
        args[self.id_name] = some_resource_id
        logger.debug(
            "Received GET request for %s %s with arguments: %s",
            self.id_name,
            some_resource_id,
            args,
        )
        return self.model_api.predict_using_model(args)


class QueryOrFileUploadResource(Resource):
    def __init__(self, model_api_obj, query_parser=None, file_parser=None):
        self.model_api = model_api_obj
        self.query_parser = query_parser
        self.file_parser = file_parser

    def get(self):
        args = self.query_parser.parse_args(
            strict=True
        )  # treat query_params and form_params as interchangeable
        logger.debug("Received GET request with arguments: %s", args)
        return self.model_api.predict_using_model(args)

    def post(self):
        if self.file_parser:
            args = self.file_parser.parse_args(strict=True)
            file_storage_obj = args["file"]
            logger.debug(
                "Received POST request with file %s of mimetype %s",
                file_storage_obj.filename,
                file_storage_obj.mimetype,
            )
        else:  # treat query_params and form_params as interchangeable
            args = self.query_parser.parse_args(strict=True)
            logger.debug("Received POST request with arguments: %s", args)
        return self.model_api.predict_using_model(args)


class ModelApi:
    """Class to plug a Data-Scientist-created model into.

    This class handles the heavy lifting of APIs for the model.

    The model is a delegate which inherits from (=implements) ModelInterface.
    It needs to provide a predict function.

    For details, see the documentation in the module `model_interface`
    """

    def __init__(self, config, application):
        """When initializing ModelApi, your model will be automatically
        retrieved from the model store based on the currently active
        configuration.

        Params:
            config:       configuration dictionary to use
            application:  flask application to use
        """
        self.model_config = config["model"]
        model_store = resource.ModelStore(config)
        self.model_wrapper = self._load_model(model_store, self.model_config)
        # Workaround (tensorflow has problem with spontaneously created threads such as with Flask):
        # https://kobkrit.com/tensor-something-is-not-an-element-of-this-graph-error-in-keras-on-flask-web-server-4173a8fe15e1
        try:
            import tensorflow as tf

            graph = tf.get_default_graph()
            self.model_wrapper.graph = graph
        except Exception as e:
            logger.debug(
                'Optional tensorflow/flask workaround for "<tensor> is not an element of this graph" problem'
                + "resulted in: %s",
                e,
            )
        else:
            logger.info(
                'Stored tensorflow model\'s graph - tensorflow/flask workaround for "<tensor> is not an element of this graph" problem'
            )
        self.datasources, self.datasinks = self._init_datasources(config)

        logger.debug("Initializing RESTful API")
        api = Api(application)

        api_name = config["api"]["name"]
        api_version = _get_major_api_version(config)
        api_url = "/{}/{}".format(api_name, api_version)

        raml = _load_raml(config)
        res_normal, res_with_id, res_file = _get_resources(raml)

        if res_file or res_normal:
            resource_urls = {"query": None, "file": None}
            parsers = {"query": None, "file": None}
            if res_normal:
                logger.debug(
                    "Adding query resource %s to api %s",
                    res_normal.path,
                    api_url,
                )
                resource_urls["query"] = api_url + res_normal.path
                parsers["query"] = _create_request_parser(res_normal)
            if res_file:
                logger.debug(
                    "Adding file-based resource %s to api %s",
                    res_file.path,
                    api_url,
                )
                resource_urls["file"] = api_url + res_file.path
                parsers["file"] = _create_request_parser(res_file)
            if (
                len(resource_urls) == 2
                and resource_urls["query"] == resource_urls["file"]
            ):
                api.add_resource(
                    QueryOrFileUploadResource,  # QueryResource,
                    resource_urls["query"],
                    resource_class_kwargs={
                        "model_api_obj": self,
                        "query_parser": parsers["query"],
                        "file_parser": parsers["file"],
                    },
                )
            else:
                for k, res_url in resource_urls.items():
                    if not res_url:
                        continue
                    api.add_resource(
                        QueryOrFileUploadResource,  # QueryResource,
                        res_url,
                        resource_class_kwargs={
                            "model_api_obj": self,
                            "query_parser": parsers["query"]
                            if k == "query"
                            else None,
                            "file_parser": parsers["file"]
                            if k == "file"
                            else None,
                        },
                    )

        if res_with_id:
            logger.debug(
                "Adding url-id resource %s to api %s",
                res_with_id.path,
                api_url,
            )
            uri_param_name = res_with_id.uri_params[-1].name
            resource_url = (
                api_url
                + res_with_id.parent.path
                + "/<string:some_resource_id>"
            )
            parser = _create_request_parser(res_with_id)
            api.add_resource(
                GetByIdResource,
                resource_url,
                resource_class_kwargs={
                    "model_api_obj": self,
                    "parser": parser,
                    "id_name": uri_param_name,
                },
            )

    def predict_using_model(self, args_dict):
        logger.debug("Prediction input %s", dict(args_dict))
        logger.info("Starting prediction")
        inner_model = self.model_wrapper.contents
        predict_args = [
            self.model_config,
            self.datasources,
            self.datasinks,
            inner_model,
            args_dict,
        ]
        if hasattr(self.model_wrapper, "graph"):
            with self.model_wrapper.graph.as_default():
                logger.info("Restored tensorflow model's graph")
                raw_output = self.model_wrapper.predict(*predict_args)
        else:
            raw_output = self.model_wrapper.predict(*predict_args)
        output = resource.to_plain_python_obj(raw_output)
        logger.debug("Prediction output %s", output)
        return output

    @staticmethod
    def _init_datasources(config):
        logger.info("Initializing datasources...")
        dso, dsi = resource.create_data_sources_and_sinks(
            config, tags="predict"
        )
        logger.info(
            "%s datasource(s) initialized: %s", len(dso), list(dso.keys())
        )
        logger.info(
            "%s datasink(s) initialized: %s", len(dsi), list(dsi.keys())
        )
        if config["api"].get("preload_datasources", False):
            logger.info("Preloading datasources...")
            for ds in dso.values():
                _ = ds.get_dataframe()

        return dso, dsi

    @staticmethod
    def _load_model(model_store, model_config):
        logger.info("Loading model...")
        model, meta = model_store.load_trained_model(model_config)
        logger.info(
            "Model loaded: {}, version: {}, created {}".format(
                meta["name"], meta["version"], meta["created"]
            )
        )

        return model


_pd_type_lookup = {
    "object": "string",
    "int64": "integer",
    "float64": "number",
    "bool": "boolean",
    "datetime64": "date",  # https://github.com/raml-org/raml-spec/blob/master/versions/raml-08/raml-08.md#date-representations
    "category": "string"  # plus enum: list(series.cat.categories)
    # RAML Types: any, object, array, union via type expression,
    #             one of the following scalar types: number, boolean, string,
    #             date-only, time-only, datetime-only, datetime, file, integer, or nil
}


def generate_raml(
    complete_conf,
    data_source_name=None,
    data_frame=None,
    resource_name="mythings",
):
    from .model_actions import _get_data_sources_and_sinks
    from urllib.parse import quote_plus

    if data_source_name is not None:
        dso, dsi = _get_data_sources_and_sinks(
            complete_conf, tags="", cache=True
        )
        df = dso[data_source_name].get_dataframe()
    elif data_frame is not None:
        df = data_frame
    else:
        raise ValueError("Please provide a data_source_name or a data_frame")
    sample = df.sample(1).reset_index(drop=True)
    api_name = complete_conf["api"]["name"]
    api_version = _get_major_api_version(complete_conf)
    url_start = f"http://127.0.0.1:5000/{quote_plus(api_name)}/{api_version}/{resource_name}?"
    url_params = []
    param_hints = """# can be false if optional, then provide a default here or be prepared to deal with missing values in your prediction
        #default: {}  # only makes sense for required: false
        #minimum: 0  # optional, maximum, minLength and others are also possible."""
    output = f"""
#%RAML 0.8
---
title: Put title of your {api_name} API here
baseUri: https://{{host}}/{api_name}/{{version}}
version: {api_version}  # new version only for API-breaking updates
documentation:
  - title: Example section title
    content: |
      Example section contents


/{resource_name}:  # This should be a plural form of what you're predicting, e.g. "/client_activations"
  get:  # We can support 'post' as well if needed (let us know if necessary)
    description: Briefly describe what {resource_name} exactly you get from this API
    queryParameters:  # For all ways to specify parameters see https://github.com/raml-org/raml-spec/blob/master/versions/raml-08/raml-08.md#named-parameters"""
    for col_name in sample.columns:
        series = sample[col_name]
        type_str = str(series.dtype)
        raml_type = _pd_type_lookup[type_str]
        example = repr(series[0])
        url_params += [quote_plus(col_name) + "=" + quote_plus(example)]
        illegal_chars = ":.,[]'\"\\ \n\t"
        quoted_col_name = (
            f"'{col_name}'"
            if any(c in illegal_chars for c in col_name)
            else col_name
        )
        cleaned_col_name = "".join(
            "_" if c in illegal_chars else c for c in col_name
        )
        output += f"""
      {quoted_col_name}:
        displayName: Friendly Name of {cleaned_col_name}
        type: {raml_type}
        description: Description of what {cleaned_col_name} really is
        example: {example}
        required: true  """ + param_hints.format(
            example
        )
        if type_str == "category":
            output += "\n" + str(list(series.cat.categories))
        param_hints = ""

    output += f"""
    responses:
      200:  # OK
        body:
          application/json:
            # This schema is optional but should fit your example prediction result below:
            schema: |
              {{
                "type": "object",
                "$schema": "http://json-schema.org/draft-03/schema",
                "id": "http://jsonschema.net",
                "required": true,
                "properties": {{
                  "prediction": {{
                    "type": "string",
                    "required": true,
                    "enum": ["Virginica", "Versicolor", "Setosa"]
                  }},
                  "probability": {{
                    "type": "number",
                    "required": false
                  }}
                }}
              }}
            # Provide an example of your prediction result:
            example: |
              {{
                "prediction": "Rainbows and Unicorns!"
              }}
  # /{{test_key}}: # This becomes relevant if you want the API user to provide e.g. ids for the model to look up data to predict for
  #   get:
  #     queryParameters:
  #       hello:
  #         description: some demo query parameter in addition to the uri param
  #         type: string
  #         required: true
  #         enum: ['metric', 'imperial']
  #         #default: 42


  # Example URL API call (to copy and paste into browser (e.g. Chrome) to test):
  # {url_start + '&'.join(url_params)}



  #########################################################################
  # Above is printed an example RAML for your data to copy/paste into your
  # RAML file and adapt to fully define your API.
  #
  # What you should do now:
  #   - Paste the above text into a <mymodel>.raml file (from the line '#%RAML 0.8')
  #   - Find and remove your target variable(s) in the RAML and example URL
  #   - Check and correct the resource name (currently /{resource_name})
  #   - Check the examples for sensitive data
  #   - Fill in the titles and descriptions, adapt as needed
  #
  # Official RAML specification: https://github.com/raml-org/raml-spec/blob/master/versions/raml-08/raml-08.md
  #########################################################################
"""
    return output
