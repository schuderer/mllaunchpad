from launchpad import ModelInterface, ModelMakerInterface
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn import tree
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Train this example from the command line:
# python clitool.py -c examples/tree_cfg.yml -t
#
# Start REST API:
# python clitool.py -c examples/tree_cfg.yml -a
#
# Example API call:
# http://127.0.0.1:5000/iris/v0?sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1


class MyExampleModelMaker(ModelMakerInterface):
    """Creates a model
    """

    def create_trained_model(self, model_conf, data_sources, old_model=None):

        df = data_sources['petals'].get_dataframe()
        X = df.drop('variety', axis=1)
        y = df['variety']
        
        my_tree = tree.DecisionTreeClassifier()
        my_tree.fit(X, y)

        finished_model = MyExampleModel(content=my_tree)

        metrics = self.test_trained_model(model_conf, data_sources, finished_model)

        return finished_model, metrics

    def test_trained_model(self, model_conf, data_sources, model):
        df = data_sources['petals_test'].get_dataframe()
        X_test = df.drop('variety', axis=1)
        y_test = df['variety']
        
        my_tree = model.content
        
        y_predict = my_tree.predict(X_test)

        acc = accuracy_score(y_test, y_predict)
        conf = confusion_matrix(y_test, y_predict).tolist()

        metrics = {'accuracy': acc, 'confusion_matrix': conf}

        return metrics


class MyExampleModel(ModelInterface):
    """Uses the created Data Science Model
    """

    def predict(self, model_conf, data_sources, args_dict):

        X = pd.DataFrame({
            'sepal.length': [float(args_dict['sepal.length'])],
            'sepal.width': [float(args_dict['sepal.width'])],
            'petal.length': [float(args_dict['petal.length'])],
            'petal.width': [float(args_dict['petal.width'])]
            })
            
        my_tree = self.content
        y = my_tree.predict(X)[0]

        return {'iris_soort': y}
