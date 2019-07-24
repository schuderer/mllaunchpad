from mllaunchpad import ModelInterface, ModelMakerInterface
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn import tree
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Train this example from the command line:
# python -m mllaunchpad -c tree_cfg.yml -t
#
# Start REST API:
# python -m mllaunchpad -c tree_cfg.yml -a
#
# Example API call:
# http://127.0.0.1:5000/iris/v0/varieties?sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1
#
# Example with URI Param (Resource ID):
# http://127.0.0.1:5000/iris/v0/varieties/12?hallo=metric
#
# Example to trigger batch prediction (not really the idea of an API...):
# http://127.0.0.1:5000/iris/v0/varieties


class MyExampleModelMaker(ModelMakerInterface):
    """Creates a model
    """

    def create_trained_model(self, model_conf, data_sources, data_sinks, old_model=None):

        df = data_sources['petals'].get_dataframe()
        X = df.drop('variety', axis=1)
        y = df['variety']

        my_tree = tree.DecisionTreeClassifier()
        my_tree.fit(X, y)

        return my_tree

    def test_trained_model(self, model_conf, data_sources, data_sinks, model):
        df = data_sources['petals_test'].get_dataframe()
        X_test = df.drop('variety', axis=1)
        y_test = df['variety']

        my_tree = model

        y_predict = my_tree.predict(X_test)

        acc = accuracy_score(y_test, y_predict)
        conf = confusion_matrix(y_test, y_predict).tolist()

        metrics = {'accuracy': acc, 'confusion_matrix': conf}

        return metrics


class MyExampleModel(ModelInterface):
    """Uses the created Data Science Model
    """

    def predict(self, model_conf, data_sources, data_sinks, model, args_dict):

        if 'test_key' in args_dict:
            # URI param example (an uri param is part in the args_dict just like any other input)
            key = args_dict['test_key']
            logger.info('Got the uri parameter (ID) %s. Looking up input data and predicting...', key)
            df = data_sources['batch_input'].get_dataframe()
            df['myid'] = df['myid'].apply(str)
            X = df.loc[df['myid'] == key]
            my_tree = model
            y = my_tree.predict(X.drop('myid', axis=1))[0]
            return {'iris_variety': y}
        elif 'sepal.length' not in args_dict or args_dict['sepal.length'] is None:
            # Batch prediction example
            logger.info('Doing batch prediction')
            X = data_sources['batch_input'].get_dataframe()
            my_tree = model
            y = my_tree.predict(X.drop('myid', axis=1))
            X['pred'] = y
            data_sinks['predictions'].put_dataframe(X)
            return {'status': 'ok'}

        # "Normal" prediction example
        logger.info('Doing "normal" prediction')
        X = pd.DataFrame({
            'sepal.length': [args_dict['sepal.length']],
            'sepal.width': [args_dict['sepal.width']],
            'petal.length': [args_dict['petal.length']],
            'petal.width': [args_dict['petal.width']]
            })

        my_tree = model
        y = my_tree.predict(X)[0]

        return {'iris_variety': y}
