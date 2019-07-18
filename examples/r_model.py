import logging
import rpy2
import rpy2.robjects as ro
import rpy2.robjects.packages as rp
import rpy2.rinterface as ri
from rpy2.robjects import pandas2ri
# from rpy2.robjects import numpy2ri
from mllaunchpad import ModelInterface, ModelMakerInterface
logger = logging.getLogger(__name__)
# numpy2ri.activate()  # vector=rpyn.ri2numpy(vector_R)
pandas2ri.activate()  # If wishing to convert explicitly for any reason, the functions are pandas2ri.py2rpy() and pandas2ri.rpy2py (rpy2 >= 3.0.0) (rpy2 2.9.4: pandas2ri.py2ri() and pandas2ri.ri2py(), which earlier were pandas2ri.pandas2ri() and pandas2ri.ri2pandas())).

if rpy2.__version__[0] == '2':  # tested with rpy2 == 2.9.4
    rpy2_v2 = True
    py2rpy = pandas2ri.py2ri
    rpy2py = pandas2ri.ri2py
else:  # tested with rpy2 == 3.0.4
    rpy2_v2 = False
    py2rpy = ro.conversion.py2rpy
    rpy2py = ro.conversion.rpy2py


def load_dependencies(model_conf):
    if not hasattr(ro.r, 'loaded_r_model_dependencies'):
        utils = rp.importr("utils")
        package_names = model_conf['r_dependencies']
        for pkg in package_names:
            loaded = ro.r.require(pkg)
            if not loaded[0]:
                logger.info('R package %s is not installed. Installing...', pkg)
                utils.install_packages(pkg)
                logger.info('Loading freshly installed R package %s...', pkg)
                ro.r.library(pkg)
            logger.info('Loaded R dependency package %s', pkg)
        ro.globalenv['loaded_r_model_dependencies'] = 1


def source_r_file(model_conf):
    if not hasattr(ro.r, 'create_trained_model') and not hasattr(ro.r, 'predict_with_trained_model'):
        r_filename = model_conf['r_file']
        logger.info("Loading R source file: %s...", r_filename)
        ro.r.source(r_filename)


def dict_to_r_list(d):
    if type(d) is not dict:
        return d
    else:
        return ro.r.list(**{key: dict_to_r_list(val) for key, val in d.items()})


def r_list_to_dict(d):
    if type(d) is ro.FactorVector:
        return [l for l in d.iter_labels()]
    elif type(d) is not ro.ListVector:
        return d
    else:
        if rpy2_v2:
            return {key: r_list_to_dict(d.rx2(key))[0] for key in d.names}  # rpy2 == 2.9.4
        else:
            return {key: r_list_to_dict(val[0]) for key, val in d.items()}


#  (rpy2 >= 3.0.x) Workaround to keep functions from being garbage-collected
aref = None
aref2 = None
def prepare_r_data_sources_and_sinks(data_sources, data_sinks, kind):
    """Makes data source/sink access functions available in R environment
    """
    if not hasattr(ro.r, 'created_data_sources_and_sinks_'+kind):
        logger.debug("Creating R get_dataframe and put_dataframe functions for %s", kind)

        @ri.rternalize
        def get_dataframe(name_vec, arg_dict=None):
            name = name_vec[0]
            logger.debug("Calling python DS %s's get_dataframe and returning R dataframe", name)
            pd_df = data_sources[name].get_dataframe(arg_dict)
            return py2rpy(pd_df)

        @ri.rternalize
        def put_dataframe(name_vec, r_df, arg_dict=None):
            name = name_vec[0]
            logger.debug("Calling python DS %s's put_dataframe with ri2py converted pandas dataframe", name)
            df = rpy2py(r_df)
            data_sinks[name].put_dataframe(df, arg_dict)

        ro.globalenv['get_dataframe'] = get_dataframe
        ro.globalenv['put_dataframe'] = put_dataframe

        # (rpy2 >= 3.0.x) Workaround to keep functions from being garbage-collected
        global aref, aref2
        aref = get_dataframe
        aref2 = put_dataframe

        ro.globalenv['created_data_sources_and_sinks_'+kind] = 1
    else:
        logger.debug("Using existing R get_dataframe and put_dataframe functions for %s", kind)


class MyExampleModelMaker(ModelMakerInterface):
    """Creates an R-based model
    """

    def create_trained_model(self, model_conf, data_sources, data_sinks, old_model=None):
        load_dependencies(model_conf)
        source_r_file(model_conf)
        prepare_r_data_sources_and_sinks(data_sources, data_sinks, 'train')

        r_model_conf = dict_to_r_list(model_conf)
        r_old_model = old_model if old_model is not None else ro.r('NULL')
        logger.debug("Calling R function test_trained_model")
        model = ro.r.create_trained_model(r_model_conf, r_old_model)
        logger.debug("Returned from R function create_trained_model")

        return model

    def test_trained_model(self, model_conf, data_sources, data_sinks, model):
        load_dependencies(model_conf)
        source_r_file(model_conf)
        prepare_r_data_sources_and_sinks(data_sources, data_sinks, 'test')

        r_model_conf = dict_to_r_list(model_conf)
        r_model = model
        logger.debug("Calling R function test_trained_model")
        r_metrics = ro.r.test_trained_model(r_model_conf, r_model)
        logger.debug("Returned from R function test_trained_model")
        metrics = r_list_to_dict(r_metrics)

        return metrics


class MyExampleModel(ModelInterface):
    """Uses the created Data Science Model
    """

    def predict(self, model_conf, data_sources, data_sinks, model, args_dict):
        load_dependencies(model_conf)
        source_r_file(model_conf)
        prepare_r_data_sources_and_sinks(data_sources, data_sinks, 'predict')

        r_args_list = dict_to_r_list(dict(args_dict))
        r_model_conf = dict_to_r_list(model_conf)
        r_model = model
        logger.debug("Calling R function predict_with_model")
        r_output = ro.r.predict_with_model(r_model_conf, r_args_list, r_model)
        logger.debug("Returned from R function predict_with_model")

        output = r_list_to_dict(r_output)


        return output
