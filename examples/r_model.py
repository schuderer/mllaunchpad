from launchpad import ModelInterface, ModelMakerInterface
import logging

logger = logging.getLogger(__name__)

# Train this example from the command line:
# python clitool.py -c examples/r_example_cfg.yml -t
#
# Start REST API:
# python clitool.py -c examples/r_example_cfg.yml -a
#
# Example API call:
# http://127.0.0.1:5000/some/v0/varieties?sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1


import rpy2.robjects as ro  # import r, pandas2ri, ListVector
import rpy2.robjects.packages as rp
import rpy2.rinterface as ri
from rpy2.robjects import pandas2ri, numpy2ri
pandas2ri.activate()  # If wishing to convert explicitly for any reason, the functions are pandas2ri.py2ri() and pandas2ri.ri2py() (they were pandas2ri.pandas2ri() and pandas2ri.ri2pandas()).
numpy2ri.activate()  # vector=rpyn.ri2numpy(vector_R)


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
        return {key: r_list_to_dict(d.rx2(key))[0] for key in d.names}


def prepare_r_data_sources_and_sinks(data_sources, data_sinks, kind):
    """Makes data source/sink access functions available in R environment
    """
    if not hasattr(ro.r, 'created_data_sources_and_sinks_'+kind):
        logger.debug("Creating R get_dataframe and put_dataframe functions for %s-ing", kind)

        def get_dataframe(name_vec, arg_dict=None):
            name = name_vec[0]
            logger.debug("Calling python DS %s's get_dataframe and returning R dataframe", name)
            pd_df = data_sources[name].get_dataframe(arg_dict)
            return pandas2ri.py2ri(pd_df)

        def put_dataframe(name_vec, r_df, arg_dict=None):
            name = name_vec[0]
            logger.debug("Calling python DS %s's put_dataframe with ri2py converted pandas dataframe", name)
            df = pandas2ri.ri2py(r_df)
            data_sinks[name].put_dataframe(df, arg_dict)

        ro.globalenv['get_dataframe'] = ri.rternalize(get_dataframe)
        ro.globalenv['put_dataframe'] = ri.rternalize(put_dataframe)

        ro.globalenv['created_data_sources_and_sinks_'+kind] = 1
    else:
        logger.debug("Using existing R get_dataframe and put_dataframe functions for %s-ing", kind)


class MyExampleModelMaker(ModelMakerInterface):
    """Creates an R-based model
    """

    def create_trained_model(self, model_conf, data_sources, data_sinks, old_model=None):
        load_dependencies(model_conf)
        source_r_file(model_conf)
        prepare_r_data_sources_and_sinks(data_sources, data_sinks, 'train')

        r_model_conf = dict_to_r_list(model_conf)
        r_old_model = old_model.content if old_model is not None else ro.r('NULL')
        logger.debug("Calling R function test_trained_model")
        model = ro.r.create_trained_model(r_model_conf, r_old_model)
        logger.debug("Returned from R function create_trained_model")

        finished_model = MyExampleModel(content=model)

        return finished_model

    def test_trained_model(self, model_conf, data_sources, data_sinks, model):
        load_dependencies(model_conf)
        source_r_file(model_conf)
        prepare_r_data_sources_and_sinks(data_sources, data_sinks, 'test')

        r_model_conf = dict_to_r_list(model_conf)
        r_model = model.content
        logger.debug("Calling R function test_trained_model")
        r_metrics = ro.r.test_trained_model(r_model_conf, r_model)
        logger.debug("Returned from R function test_trained_model")
        metrics = r_list_to_dict(r_metrics)

        return metrics


class MyExampleModel(ModelInterface):
    """Uses the created Data Science Model
    """

    def predict(self, model_conf, data_sources, data_sinks, args_dict):
        load_dependencies(model_conf)
        source_r_file(model_conf)
        prepare_r_data_sources_and_sinks(data_sources, data_sinks, 'predict')

        r_args_dict = dict_to_r_list(dict(args_dict))
        r_model_conf = dict_to_r_list(model_conf)
        r_model = self.content
        logger.debug("Calling R function predict_with_model")
        r_output = ro.r.predict_with_model(r_model_conf, r_args_dict, r_model)
        logger.debug("Returned from R function predict_with_model")

        print("r_output", r_output)
        print("r_output[0]", r_output[0])

        output = r_list_to_dict(r_output)


        return output
