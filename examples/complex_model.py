import pandas as pd
from sklearn import tree
from sklearn.metrics import accuracy_score, confusion_matrix
from launchpad import ModelInterface, ModelMakerInterface
import logging

logger = logging.getLogger(__name__)

# Train this example from the command line:
# python clitool.py -c examples/complex_cfg.yml -t
#
# Start REST API:
# python clitool.py -c examples/complex_cfg.yml -a
#
# Example API call:
# http://127.0.0.1:5000/guessiris/v0?x=3&sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1


def data_prep(X):
    # prepping features, maybe parsing strange formats, imputing, cleaning text ...
    return X


class MyModelMaker(ModelMakerInterface):
    """
    """

    def create_trained_model(self, model_conf, data_sources, old_model=None):
        # demo: get the database data source
        limit = model_conf['train_options']['num_ora_rows']
        dbdf = data_sources['panel'].get_dataframe(arg_dict={'limit': limit})
        print(dbdf)

        # just for lolz
        number_to_add = model_conf['train_options']['magic_number']
        my_lame_predictor = lambda x: x + number_to_add

        # train a tree as a demo
        df = data_sources['petals'].get_dataframe()
        X_train = df.drop('variety', axis=1)
        y_train = df['variety']

        # optional data prep/feature creation/refinement here...
        my_tree = tree.DecisionTreeClassifier()
        my_tree.fit(X_train, y_train)

        model_contents = {'lame_pred': my_lame_predictor, 'petal_pred': my_tree}
        finished_model = MyModel(content=model_contents)

        return finished_model

    def test_trained_model(self, model_conf, data_sources, model):
        df = data_sources['petals_test'].get_dataframe()
        X_test = df.drop('variety', axis=1)
        y_test = df['variety']

        my_tree = model.content['petal_pred']

        y_predict = my_tree.predict(X_test)

        acc = accuracy_score(y_test, y_predict)
        conf = confusion_matrix(y_test, y_predict).tolist()
        metrics = {'accuracy': acc, 'confusion_matrix': conf}

        return metrics


class MyModel(ModelInterface):
    """Does some simple prediction
    """

    def predict(self, model_conf, data_sources, args_dict):
        logger.info('Hey, look at me -- I\'m carrying out a prediction')

        # Do some lame prediction (= addition)
        x_raw = int(args_dict['x'])  # todo sanitize

        # optional data prep/feature creation for x here...
        x = data_prep(x_raw)

        name_df = data_sources['first_names'].get_dataframe()
        random_name = name_df.sample(n=1)['name'].values[0]

        lame_predictor = self.content['lame_pred']
        y = lame_predictor(x)

        # Also try iris petal-based prediction:
        # to test: 127.0.0.1:5000/mypredict?x=3&sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1
        petal_predictor = self.content['petal_pred']
        X2 = pd.DataFrame({
            'sepal.length': [float(args_dict['sepal.length'])],
            'sepal.width': [float(args_dict['sepal.width'])],
            'petal.length': [float(args_dict['petal.length'])],
            'petal.width': [float(args_dict['petal.width'])]
            })
        y2 = petal_predictor.predict(X2)[0]

        return {'the_result_yo': y, 'random_name': random_name, 'iris_variety': y2}
