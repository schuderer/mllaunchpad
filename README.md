# launchpad
ML Launchpad is a lightweight machine learning model life cycle framework.

What this means is that it creates a separation between machine learning models, and their environment. This way, you can run your model with different data sources and on different environments, by just swapping out the configuration, no code changes required. It also makes it very easy to make your model available as a business-facing *RESTful API* without extra coding.

(As of now, it is just an importable python package, not a deployable package -- yet!)

Currently, some basic model life cycle management is supported. Training automatically persists a model, including its metrics, in the model store, and automatically retreives it for launching its API or re-training. Previous models are backed up.

- [ ] better description of what problem ML Launchpad solves

## Getting started

Download and unzip the repository as a zip file or clone the repository using git:
```bash
$ git clone git@github.com:schuderer/launchpad.git
```
Go to the `launchpad` directort in a terminal:
```bash
$ cd launchpad
```

If you have `pipenv` available (if not, it can be easily installed using `pip install pipenv`), create the environment with all the dependencies.
```bash
$ pipenv install
```
(Use `pipenv install --dev` if you want to try out the examples -- not all development dependencies are needed for all examples, so don't sweat it if there are problems installing all of them)

Don't have `pipenv`? Have a look at the file `Pipfile` to see which dependencies might need installing.

## What do I see?

The subfolder `launchpad` is the actual ML Launchpad package. The rest are examples and development tools.

The subfolder `examples` contains a few example model implementations. Look here for inspiration on how to use this package. Every model here consists of at least three files:
- `<examplename>_model.py`: the example's actual model code
- `<examplename>_cfg.yml`: the example's configuration file
- `<examplename>.raml`: example's RESTful API specification. Used, among others, to parse and validate parameters.
- There are also some extra files, like CSV files to use, or datasource extensions

The subfolder `testserver` contains an example for running a REST API in gunicorn behind nginx.

## Try Out the Examples

To train a very, *very* simple example model whose job it is to add two numbers, use the command:
```bash
$ python -m launchpad -c examples/addition_cfg.yml -t
```
(We give it a config file after the `-c` parameter, and `-t` is short for the command `--train`. There's also a parameter `-h` to print help)

Some log information is printed (you can give it a log-config file to change this, see examples/logging_cfg.yml). At the end, it should say "Created and stored trained model", followed by something about metrics.

This created a model_store if it didn't exist yet (which for now is just a directory). For our examples, the model store is conveniently located in the same directory. It contains our persisted `addition` model and its metadata.

To re-test the previously trained model, use the command `-r`:
```bash
$ python -m launchpad -c examples/addition_cfg.yml -r
```

To run a (debugging-only!) REST API for the model, use the command `-a`:
```bash
$ python -m launchpad -c examples/addition_cfg.yml -a
```

To quickly try out out our fancy addition model API, open this link in a browser: http://127.0.0.1:5000/add/v0/sum?x1=3&x2=2
(`curl http://127.0.0.1:5000/add/v0/sum?x1=3&x2=2` on the command line)

If you get `ModuleNotFoundError: No module named 'launchpad'` (in `launchpad/__main__.py`), try to start flask the following way:
```bash
$ set FLASK_APP=launchpad/wsgi.py:application
$ set LAUNCHPAD_CFG=examples/addition_cfg.yml
$ flask run
```
This appears to be connected to Flask restarting in different ways on different
installations. If you know what this is about, [please let us know](https://github.com/schuderer/launchpad/issues/30)

### What next?

Have a look at the `addition` example's python code (and comments), its yml config, then look at the other examples. First, we suggest the `iris` example for intermediate complexity (although its prediction code does quite some complex stuff to be compatible with three different kinds of prediction usage, which is not really that realistic).

If you are wondering about the RAML file (which is a RESTful API specification standard that is used in some corporate environments, and a good idea in general), also look at the `-g` (generate raml) command line parameter, which does a lot of work (almost all of it, in fact) for getting you started with a first RAML.

## Is it for me?

- [ ] fill in this section
