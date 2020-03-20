import logging

from mllaunchpad import ModelInterface, ModelMakerInterface, order_columns
# from sklearn import tree
# from sklearn.metrics import accuracy_score, confusion_matrix


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

    def create_trained_model(
        self, model_conf, data_sources, data_sinks, old_model=None
    ):
        # df_unordered = data_sources["petals"].get_dataframe()

        # Ordering columns is strongly recommended to guarantee consistency between training and API calls:
        # df = order_columns(df_unordered)

        ...
        model = ...

        return model

    def test_trained_model(self, model_conf, data_sources, data_sinks, model):
        # df_unordered = data_sources["petals_test"].get_dataframe()

        # Ordering columns is strongly recommended to guarantee consistency between training and API calls:
        # df = order_columns(df_unordered)

        ...
        metrics = ...

        return metrics


class MyExampleModel(ModelInterface):
    """Uses the created Data Science Model
    """

    def predict(self, model_conf, data_sources, data_sinks, model, args_dict):
        # Ordering columns is strongly recommended to guarantee consistency between training and API calls:
        # df = order_columns(pd.DataFrame(args_dict, index=[0]))

        ...
        output = ...

        return output
