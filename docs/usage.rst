==============================================================================
Usage
==============================================================================

Tutorial
------------------------------------------------------------------------------

This tutorial will guide you through using ML Launchpad to publish
a small machine learning project as a Web API.

Let's assume that you have developed a Python script called ``tree_script.py``
which contains the code to train, test and apply your model from Python::

    my_project/
        iris_train.csv
        iris_holdout.csv
        tree_script.py

Contents of ``tree_script.py``:

.. code-block:: python

    import sys

    import pandas as pd
    from sklearn import tree
    from sklearn.metrics import accuracy_score, confusion_matrix

    def train():
        df = pd.read_csv('iris_train.csv')
        X = df.drop('variety', axis=1)
        y = df['variety']
        model = tree.DecisionTreeClassifier()
        model.fit(X, y)
        return model


    def test(model):
        df = pd.read_csv('iris_holdout.csv')
        X_test = df.drop('variety', axis=1)
        y_test = df['variety']
        y_predict = model.predict(X_test)
        acc = accuracy_score(y_test, y_predict)
        conf = confusion_matrix(y_test, y_predict).tolist()
        metrics = {'accuracy': acc, 'confusion_matrix': conf}
        return metrics


    def predict(model, args_dict):
        # Create DF explicitly. No guarantee that dict keys are in correct order
        X = pd.DataFrame({
            'sepal.length': [args_dict['sepal.length']],
            'sepal.width': [args_dict['sepal.width']],
            'petal.length': [args_dict['petal.length']],
            'petal.width': [args_dict['petal.width']]
            })
        y = model.predict(X)[0]
        return {'prediction': y}


    if __name__ == '__main__':
        args = dict(zip([n for n in sys.argv[1::2]], [float(v) for v in sys.argv[2::2]]))
        my_model = train()
        print('metrics:', test(my_model))
        pred = predict(my_model, args)
        print('prediction result:', pred)

        # Example:
        # $ python tree_script.py sepal.length 3 sepal.width 2.7 petal.length 4.5 petal.width 3.5
        # metrics: {'accuracy': 0.95, 'confusion_matrix': [[6, 0, 0], [0, 7, 0], [0, 1, 6]]}
        # prediction result: {'prediction': 'Virginica'}


This script can be called from the command line and
guesses the variety of iris from some physical measurements provided
as command line arguments. It somewhat wastefully trains a new model
every time it is called, and does not check the validity of the arguments
at all. Besides making the model available as a Web API, ML Launchpad will
also solve these two problems.

To use ML Launchpad, :doc:`install <installation>` it first using:

.. code-block:: console

    $ pip install mllaunchpad

Now, we'll create a new Python file called ``tree_model.py`` in which we will fill in the
blanks::

    my_project/
        iris_train.csv
        iris_holdout.csv
        tree_script.py
        tree_model.py

The file ``tree_model.py`` looks like this at first:

.. code-block:: python

    from mllaunchpad import ModelInterface, ModelMakerInterface
    from sklearn.metrics import accuracy_score, confusion_matrix
    from sklearn import tree
    import pandas as pd
    import logging

    logger = logging.getLogger(__name__)

    class MyTreeModelMaker(ModelMakerInterface):
        """Creates a Iris prediction model"""

        def create_trained_model(self, model_conf, data_sources, data_sinks, old_model=None):
            ...

            return model

        def test_trained_model(self, model_conf, data_sources, data_sinks, model):
            ...

            return metrics


    class MyTreeModel(ModelInterface):
        """Uses the created Iris prediction model"""

        def predict(self, model_conf, data_sources, data_sinks, model, args_dict):
            ...

            return output


You can find a template like this in ML Launchpad's examples
(`download the examples <https://minhaskamal.github.io/DownGit/#/home?url=https://github.com/schuderer/mllaunchpad/tree/master/examples>`_,
or copy-paste from ``TEMPLATE_model.py`` on `GitHub <https://github.com/schuderer/mllaunchpad/blob/master/examples/TEMPLATE_model.py>`_).

The three methods
:meth:`~mllaunchpad.model_interface.ModelMakerInterface.create_trained_model`,
:meth:`~mllaunchpad.model_interface.ModelMakerInterface.test_trained_model`
and :meth:`~mllaunchpad.model_interface.ModelInterface.predict`
correspond to the three functions in our script above.
We can essentially copy and paste the contents of our three functions into
those, but we will need to change some details to make the code work with
ML Launchpad.

Here, we'll make use of the method arguments ``data_sources`` and ``model``.
See :mod:`~mllaunchpad.model_interface` for details on all available
parameters.

If we call our training :class:`~mllaunchpad.resource.DataSource` ``petals`` and our test
DataSource ``petals_test``, our completed ``tree_model.py`` looks
like this (we highlight changed code with ``#comments``):

.. code-block:: python

    from mllaunchpad import ModelInterface, ModelMakerInterface
    from sklearn.metrics import accuracy_score, confusion_matrix
    from sklearn import tree
    import pandas as pd
    import logging

    logger = logging.getLogger(__name__)

    class MyTreeModelMaker(ModelMakerInterface):
        """Creates a Iris prediction model"""

        def create_trained_model(self, model_conf, data_sources, data_sinks, old_model=None):
            # use data_source instead of reading CSV ourselves:
            df = data_sources['petals'].get_dataframe()
            X = df.drop('variety', axis=1)
            y = df['variety']
            model = tree.DecisionTreeClassifier()
            model.fit(X, y)
            return model

        def test_trained_model(self, model_conf, data_sources, data_sinks, model):
            # use data_source instead of reading CSV ourselves:
            df = data_sources['petals_test'].get_dataframe()
            X_test = df.drop('variety', axis=1)
            y_test = df['variety']
            y_predict = model.predict(X_test)
            acc = accuracy_score(y_test, y_predict)
            conf = confusion_matrix(y_test, y_predict).tolist()
            metrics = {'accuracy': acc, 'confusion_matrix': conf}
            return metrics


    class MyTreeModel(ModelInterface):
        """Uses the created Iris prediction model"""

        def predict(self, model_conf, data_sources, data_sinks, model, args_dict):
            # No changes required
            X = pd.DataFrame({
                'sepal.length': [args_dict['sepal.length']],
                'sepal.width': [args_dict['sepal.width']],
                'petal.length': [args_dict['petal.length']],
                'petal.width': [args_dict['petal.width']]
                })
            y = model.predict(X)[0]
            return {'prediction': y}

So we are now getting our data from the ``data_source`` arguments
instead of directly from ``csv`` files, and we get our ``model``
object passed as an argument, same as before.

The three methods return the same things as our own functions:

* :meth:`~mllaunchpad.model_interface.ModelMakerInterface.create_trained_model`
  returns a trained model object (can be pretty much anything),

* :meth:`~mllaunchpad.model_interface.ModelMakerInterface.test_trained_model`
  returns a ``dict`` with
  metrics (can also contain ``lists``, numpy arrays or pandas DataFrames), and

* :meth:`~mllaunchpad.model_interface.ModelInterface.predict`
  returns a prediction (usually a ``dict``, but
  can also contain ``lists``, numpy arrays or pandas DataFrames).


Next, we will configure some extra info about our model,
as well as tell ML Launchpad where to find
the ``petal`` and ``petal_test`` :class:`~mllaunchpad.resource.DataSource` s.

Create a file called ``tree_cfg.yml``::

    my_project/
        iris_train.csv
        iris_holdout.csv
        tree_model.py
        tree_cfg.yml

(We're done with our original ``tree_script.py`` so I've removed it)

Contents of ``tree_cfg.yml``:

.. code-block:: yaml

    datasources:
      petals:
        type: csv
        path: ./iris_train.csv  # The string can also be a URL. Valid URL schemes include http, ftp, s3, and file.
        expires: 0  # -1: never (=cached forever), 0: immediately (=no caching), >0: time in seconds.
        options: {}
        tags: train
      petals_test:
        type: csv
        path: ./iris_holdout.csv
        expires: 3600
        options: {}
        tags: test

    model_store:
      location: ./model_store  # Just in current directory for now

    model:
      name: TreeModel
      version: '0.0.1'  # use semantic versioning (<breaking>.<adding>.<fix>)
      module: tree_model  # same as file name without .py
      train_options: {}
      predict_options: {}

    api:
      name: iris  # name of the service api
      version: '0.0.1'  # use semantic versioning (breaking.adding.fix), first segment will be used in url as e.g. .../v1/...
      raml: tree.raml
      preload_datasources: False  # Load datasources into memory before any predictions. Only makes sense with caching.


Here, we define our ``datasources`` so ML Launchpad knows where to find the
data we refer to from our model. Besides ``csv`` files,
other types of DataSources are supported, and
:ref:`extending DataSources <extending>` is also possible.
(see module :class:`~mllaunchpad.resource` for more information on supported
builtin :class:`~mllaunchpad.resource.DataSources`).

The ``model_store`` is just a directory where all trained models will
be stored together with their metrics.

The ``model`` section gives our model a name and version which will be
used to uniquely identify it when saving/loading. Here, we also
provide the importable name of our ``tree_model.py``, which is just
``tree_model``. If it were in a package (directory) called ``something``,
we would write ``something.tree_model`` instead.
It's a good idea to make sure our model is in Pythons path (``sys.path``
or ``PYTHONPATH``) so it can be found when ML Launchpad wants to import it.

The ``api`` section provides details on the Web API we want to publish.
This section is maybe surprisingly empty. The reason is that the API
definition is off-loaded into a *RESTful API Markup Language* (RAML) file.

You can genereate a RAML file using the command line tool that has
been installed when you installed ML Launchpad:

.. code-block:: console

    $ mllaunchpad --config=tree_cfg.yml --generateraml=petals >tree.raml

This creates the API definition file ``tree.raml`` using the columns
and their types in the ``petals`` datasource for defining parameters.
We still need to adapt this file a little because it also lists
our target variable ``variety`` as an input parameter, which we don't
want, so we edit the file and remove these lines:

.. code-block:: yaml

      variety:
        displayName: Friendly Name of variety
        type: string
        description: Description of what variety really is
        example: 'Versicolor'
        required: true

This is the only change which is necessary from a technical standpoint.
Feel free to read the RAML file and improve the template descriptions
there, correct ``mythings`` to something that makes sense, like
``varieties``, adapt the output format to what you want to use, and so on.

Our model is done! Let's try it out.

.. code-block:: console

    $ mllaunchpad --config=tree_cfg.yml --train

Now we have a trained model in our ``model_store``. Let's run the Web API:

.. code-block:: console

    $ mllaunchpad --config=tree_cfg.yml --api

We can find a test URL in our generated ``tree.raml``. Just remove
the ``&variety=...`` part, and open the link
http://127.0.0.1:5000/iris/v0/mythings?sepal.length=5.6&sepal.width=2.7&petal.length=4.2&petal.width=1.3
e.g. in Chrome. You can see the result of our model's prediction
immediately:

.. code-block:: json

    {
        "prediction": "Versicolor"
    }

Automatic input validation is included for free. Try changing the URL to
provide a string value instead of a number, or remove one of the parameters,
and you get a message explaining what is wrong.

What we have now is what is called RESTful API. Web APIs like this are easy
to use by other systems or web sites to include your model's
predictions in their functionality.

Here's a quick hacked-together HTML page which makes the predictions
available to an end user:

.. code-block:: html

    <!DOCTYPE html>
    <html><body>
        <h2>Iris Tree Demo</h2>
        <div>
            Sepal Width: <input id="sl" type="range" min="0.1" max="7" step="0.1"><br>
            Sepal Length: <input id="sw" type="range" min="0.1" max="7" step="0.1"><br>
            Petal Length: <input id="pl" type="range" min="0.1" max="7" step="0.1"><br>
            Petal Width: <input id="pw" type="range" min="0.1" max="7" step="0.1"><br>
        </div>
        <div id="output"></div>
        <script>
            function predict() {
                let sl = document.querySelector('#sl').value;
                let sw = document.querySelector('#sw').value;
                let pl = document.querySelector('#pl').value;
                let pw = document.querySelector('#pw').value;
                fetch(`http://127.0.0.1:5000/iris/v0/mythings?sepal.length=${sl}&sepal.width=${sw}&petal.length=${pl}&petal.width=${pw}`)
                .then(function(response) {
                    document.querySelector('#output').innerHTML = response.json();
                })
                .then(function(myJson) {
                    console.log(JSON.stringify(myJson));
                });
            }
            let inputs = document.querySelectorAll('input');
            for (let input of inputs) {
                input.addEventListener('change', predict, false);
            }
        </script>
    </body></html>


To learn more, have a look at the examples provided in `mllaunchpad's GitHub repository <https://github.com/schuderer/mllaunchpad/>`_
(`examples as zip file <https://minhaskamal.github.io/DownGit/#/home?url=https://github.com/schuderer/mllaunchpad/tree/master/examples>`_).
