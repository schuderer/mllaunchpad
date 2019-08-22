from mllaunchpad import ModelInterface, ModelMakerInterface
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn import tree
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Train this example from the command line:
# python -m mllaunchpad -c TEMPLATE_cfg.yml -t
#
# Start REST API:
# python -m mllaunchpad -c TEMPLATE_cfg.yml -a
#
# Example API call:
# http://127.0.0.1:5000/TEMPLATE/v0/varieties?sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1


class MyExampleModelMaker(ModelMakerInterface):
    """Creates a model
    """

    def create_trained_model(self, model_conf, data_sources, data_sinks, old_model=None):
        df = data_sources['petals'].get_dataframe()

        ...

        return model

    def test_trained_model(self, model_conf, data_sources, data_sinks, model):
        ...

        return metrics


class MyExampleModel(ModelInterface):
    """Uses the created Data Science Model
    """

    def predict(self, model_conf, data_sources, data_sinks, model, args_dict):
        ...

        return output
