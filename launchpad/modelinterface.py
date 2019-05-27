import abc
import logging

logger = logging.getLogger(__name__)


class ModelInterface(abc.ABC):
    """Abstract model interface for Data-Scientist-created models.
    Please inherit from this class when creating your model to make
    it usable for ModelApi.

    When initializing your derived model, pass it an object
    which contains what is needed for prediction (usually your trained regressor
    or classifier, but can be anything). It is stored in self.obj.
    """

    def __init__(self, content=None):
        """If you overwrite __init__, please call super().__init__(...)
        at the beginning. Otherwise, you need to assign self.content to the
        content parameter manually in __init__.

        Params:
            content:  any object that is needed for prediction (usually a trained
                      classifier or predictor)
        """
        self.content = content


    @abc.abstractmethod
    def predict(self, model_conf, data_sources, argsDict):
        """Implement this method, including data prep/feature creation based on argsDict.
        argsDict can also contain an id which the model can use to fetch data
        from any data_sources.
        (Feel free to put common code for preparing data into another function,
        class, library, ...)

        Params:
            model_conf:   the model configuration dict from the config file
            data_sources: dict containing the data sources
            argsDict:     parameters the API was called with, dict of strings
                          (any type conversion needs to be done by you)

        Return:
            Prediction result as a dictionary/list structure which will be
            automatically turned into JSON.
        """
        ...


    def __del__(self):
        """Clean up any resources (temporary files, sockets, etc.).
        If you overtwrite this method, please call super().__del__() at the beginning.
        """
        ...


class ModelMakerInterface(abc.ABC):
    """Abstract model factory interface for Data-Scientist-created models.
    Please inherit from this class and put your training code into the
    method "createTrainedModel". This method will be called by the framework when
    your model needs to be (re)trained.

    Why not simply use static methods?
        We want to make it possible for createTrainedModel to pass extra info
        testTrainedModel without extending the latter with optional keyword
        arguments that might be confusing for the 90% of cases where they are
        not needed. So we rely on the smarts of the person inheriting from this
        class to find a solution/shortcuts if they e.g. want to do the train/test
        split themselves.
    """

    @abc.abstractmethod
    def createTrainedModel(self, model_conf, data_sources, old_model=None):
        """Implement this method, including data prep/feature creation.
        (Feel free to put common code for preparing data into another function,
        class, library, ...)

        Params:
            model_conf:   the model configuration dict from the config file
            data_sources: dict containing the data sources (this includes your
                          train/validation/test data), as configured in the
                          config file
            old_model:    contains an old model, if it exists, which can be used
                          for incremental training. default: None

        Return:
            Tuple of modelForRunning and metrics
            where "modelForRunning" is an instance of your ModelInterface-derived
            class (which you passed your trained classifier/... as constructor parameter),
            and "metrics" is a dict of metrics (like 'accuracy', 'f1', 'confusion_matrix',
            etc.), as it is produced by the method "testTrainedModel".
        """
        ...

    @abc.abstractmethod
    def testTrainedModel(self, model_conf, data_sources, model):
        """Implement this method, including data prep/feature creation.
        This method will be called to re-test a model, e.g. to check whether
        it has to be re-trained. You should also use this method for your
        own testing after training.
        (Feel free to put common code for preparing data into another function,
        class, library, ...)

        Params:
            model_conf:   the model configuration dict from the config file
            data_sources: dict containing the data sources (this includes your
                          train/validation/test data), as configured in the
                          config file
            model:        instance of your model object (inherited from ModelInterface)

        Return:
            Return a dict of metrics (like 'accuracy', 'f1', 'confusion_matrix',
            etc.)
        """
        ...
