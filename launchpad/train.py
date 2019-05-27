from . import resource
from . import modelinterface
import logging

logger = logging.getLogger(__name__)


def _get_model_maker(complete_conf):
    """Locate and instantiate class of data-scientist-provided ModelMaker
    (which the data scientist inherited from ModelMakerInterface).
    For this to work, your model module (.py file) needs to be in python's
    sys.path (usually the case).
    Also set the config's model: module property accordingly.
    TODO: maybe add a module_location property or something so that it automatically
    gets appended to the sys.path.

    Params:
        complete_conf: the configuration dict

    Returns:
        instance of data scientist's ModelMaker model factory object
    """
    logger.debug('Locating and instantiating ModelMaker...')

    __import__(complete_conf['model']['module'])

    classes = modelinterface.ModelMakerInterface.__subclasses__()
    if len(classes) != 1:
        raise ValueError('The configured model module (.py file) must contain ' +
                         'one ModelMakerInterface-inheriting class definition, but contains {}.'
                         .format(len(classes)))

    mm_cls = classes[0]
    logger.debug('Found ModelMaker class named %s', mm_cls)

    mm = mm_cls()
    logger.debug('Instantiated ModelMaker object %s', mm)

    return mm


def train_model(complete_conf):
    logger.debug('Creating trained model...')
    user_mm = _get_model_maker(complete_conf)

    ds = resource.create_data_sources(complete_conf, tag='train')

    model_conf = complete_conf['model']
    model, metrics = user_mm.create_trained_model(model_conf, ds)

    if not isinstance(model, modelinterface.ModelInterface):
        logger.warning('Model\'s class is not a subclass of ModelInterface: %s', model)

    model_store = resource.ModelStore(complete_conf)
    model_store.dump_trained_model(complete_conf, model, metrics)

    logger.info('Created and stored trained model %s, version %s, metrics %s',
                model_conf['name'], model_conf['version'], metrics)

    return model, metrics


def retest_model(complete_conf):
    logger.debug('Retesting existing trained model...')
    user_mm = _get_model_maker(complete_conf)

    ds = resource.create_data_sources(complete_conf, tag='test')

    model_conf = complete_conf['model']
    model_store = resource.ModelStore(complete_conf)
    model, metadata = model_store.load_trained_model(model_conf)

    metrics_test = user_mm.test_trained_model(model_conf, ds, model)

    model_store.update_model_metrics(model_conf, metrics_test)

    logger.info('Retested existing model %s, version %s, new metrics %s',
                model_conf['name'], model_conf['version'], metrics_test)

    return metrics_test
