# -*- coding: utf-8 -*-

import abc
import logging

logger = logging.getLogger(__name__)


class ModelMakerInterface(abc.ABC):
    """Abstract model factory interface for Data-Scientist-created models.
    Please inherit from this class and put your training code into the
    method "create_trained_model". This method will be called by the framework when
    your model needs to be (re)trained.

    Why not simply use static methods?
        We want to make it possible for create_trained_model to pass extra info
        test_trained_model without extending the latter with optional keyword
        arguments that might be confusing for the 90% of cases where they are
        not needed. So we rely on the smarts of the person inheriting from this
        class to find a solution/shortcuts if they want to do more difficult
        things e.g. want to do the train/test split themselves.
    """

    @abc.abstractmethod
    def create_trained_model(
        self, model_conf, data_sources, data_sinks, old_model=None
    ):
        """Implement this method, including data prep/feature creation.
        No need to test your model here. Put testing code in test_trained_model, which
        will be called automatically after training.
        (Feel free to put common code for preparing data into another function,
        class, library, ...)

        Params:
            model_conf:   the model configuration dict from the config file
            data_sources: dict containing the data sources (this includes your train/validation/test data), as configured in the config file
            data_sinks:   dict containing the data sinks, as configured in the config file. Usually unused when training.
            old_model:    contains an old model, if it exists, which can be used for incremental training. default: None

        Return:
            The trained model/data/anything which you want to use in the predict()
            function. (usually simply a fitted model object, but can be anything,
            like a dict of several models, a model with some extra info, etc.)
            (Whatever you return here gets automatically stuffed into your
            ModelInterface-inherited object and is accessible there using
            predict's model parameter (or the self.contents attribute.))
        """
        ...

    @abc.abstractmethod
    def test_trained_model(self, model_conf, data_sources, data_sinks, model):
        """Implement this method, including data prep/feature creation.
        This method will be called to re-test a model, e.g. to check whether
        it has to be re-trained.
        (Feel free to put common code for preparing data into another function,
        class, library, ...)

        Params:
            model_conf:   the model configuration dict from the config file
            data_sources: dict containing the data sources (this includes your train/validation/test data), as configured in the config file
            data_sinks:   dict containing the data sinks, as configured in the config file. Usually unused when testing.
            model:        your model object (whatever you returned in create_trained_model)

        Return:
            Return a dict of metrics (like 'accuracy', 'f1', 'confusion_matrix', etc.)
        """
        ...


class ModelInterface(abc.ABC):
    """Abstract model interface for Data-Scientist-created models.
    Please inherit from this class when creating your model to make
    it usable for ModelApi.

    You don't need to create this object yourself when training.
    It is created automatically and the model/info returned from create_trained_model
    is made accessible to you through the self.contents attribute.
    """

    def __init__(self, contents=None):
        """If you overwrite __init__, please call super().__init__(...)
        at the beginning. Otherwise, you need to assign self.contents to the
        contents parameter manually in __init__.

        Params:
            contents:  any object that is needed for prediction (usually a trained
                      classifier or predictor). It is passed to the predict()
                      method as the "model" parameter for convenience.
        """
        self.contents = contents

    @abc.abstractmethod
    def predict(self, model_conf, data_sources, data_sinks, model, args_dict):
        """Implement this method, including data prep/feature creation based on argsDict.
        argsDict can also contain an id which the model can use to fetch data
        from any data_sources.
        (Feel free to put common code for preparing data into another function,
        class, library, ...)

        Params:
            model_conf:   the model configuration dict from the config file
            data_sources: dict containing the data sources
            data_sinks:   dict containing the data sinks, as configured in the config file.
            model:        your model object (whatever you returned in create_trained_model)
            argsDict:     parameters the API was called with, dict of strings (any type conversion needs to be done by you)

        Return:
            Prediction result as a dictionary/list structure which will be automatically turned into JSON.
        """
        ...

    def __del__(self):
        """Clean up any resources (temporary files, sockets, etc.).
        If you overwrite this method, please call super().__del__() at the beginning.
        """
        ...
