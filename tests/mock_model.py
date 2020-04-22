# Project imports
from mllaunchpad import ModelInterface, ModelMakerInterface


prediction_output = "it worked"


class MockModelClass(ModelInterface):
    def predict(self, model_conf, data_sources, data_sinks, model, args_dict):
        return prediction_output


class MockModelMakerClass(ModelMakerInterface):
    def create_trained_model(
        self, model_conf, data_sources, data_sinks, old_model=None
    ):
        return {}

    def test_trained_model(self, model_conf, data_sources, data_sinks, model):
        return {}
