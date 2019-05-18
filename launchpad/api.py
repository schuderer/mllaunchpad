from flask import Flask, request  # import gunicorn  # usable for prod, maybe use with nginx
from flask_restful import Resource, Api # TODO: install watchdog for flask to use (no polling = fewer cpu cycles)
from . import resource
import logging

logger = logging.getLogger(__name__)


class FlaskPredictionResource(Resource):
    # Adapted from https://flask-restful.readthedocs.io/en/latest/quickstart.html
    def __init__(self, modelApiObj):
        self.modelApi = modelApiObj

    def get(self):  # todo: optional resource identifier like kltid?
        args = request.args
        logger.debug("Received GET request with arguments: %s", args)
        return self.modelApi.predict_using_model(args)


class ModelApi():
    """Class to plug a Data-Scientist-created model into.

    This class handles the heavy lifting of APIs, config, etc for the model.

    The model is a delegate which inherits from (=implements) ModelInterface.
    It needs to provide certain functionality:
       - a predict function
    """

    def __init__(self, conf):
        """When initializing ModelApi, your model will be automatically
        retrieved from the model store based on the currently active
        configuration.

        Params:
            conf:   configuration dictionary to use
        """
        self.config = conf

        self.datasources = self.init_datasources()

        self.model = self.load_model()


    def init_datasources(self):
        logger.info("Initializing datasources...")
        ds = resource.create_data_sources(self.config, tag="predict")
        logger.info("%s datasource(s) initialized: %s", len(ds), list(ds.keys()))

        return ds


    def load_model(self):
        logger.info("Loading model...")
        self.model_store = resource.ModelStore(self.config)
        self.model_config = self.config['model']
        model, meta = self.model_store.load_trained_model(self.model_config)
        logger.info("Model loaded: {}, version: {}, created {}".format(meta['name'], meta['version'], meta['created']))

        return model


    def predict_using_model(self, argsDict):
        logger.debug("Prediction input %s", dict(argsDict))
        logger.info("Starting prediction")
        output = self.model.predict(self.model_config, self.datasources, argsDict)
        logger.debug("Prediction output %s", output)
        return output


    def run(self):
        logger.info("Starting Flask server")
        self.app = Flask(__name__)
        api = Api(self.app)
        api.add_resource(FlaskPredictionResource,
                         '/'+self.config['api']['resource_name'],
                         resource_class_kwargs={'modelApiObj': self})
        self.app.run(debug=True)
        logger.info("Flask server stopped")
