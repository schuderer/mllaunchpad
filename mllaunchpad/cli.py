# -*- coding: utf-8 -*-

"""This module provides the command line interface for ML Launchpad"""

# Stdlib imports
import json
from logging import Logger
import sys

# Third-party imports
import click
from flask import Flask

# Application imports
import mllaunchpad as lp
from mllaunchpad import logutil
from mllaunchpad.api import generate_raml
from mllaunchpad.api import ModelApi


# Fix for click using the wrong name if run using `python -m mllaunchpad`
# Alsoo see: https://github.com/pallets/click/issues/365
sys.argv[0] = "mllaunchpad"


# TODO: Migrate to @dataclass when dropping support for Python 3.6
class Settings:
    def __init__(self):
        self.verbose: bool = False
        self.logger: Logger = None
        self.conf_file: str = None

    @property
    def config(self):
        if not hasattr(self, "_config"):
            if self.conf_file:
                self._config = lp.get_validated_config(self.conf_file)
            else:
                self._config = lp.get_validated_config()
        return self._config


pass_settings = click.make_pass_decorator(Settings, ensure=True)


@click.group()
@click.version_option(prog_name="ML Launchpad")
@click.option("--verbose", "-v", is_flag=True, help="Print debug messages.")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Use this configuration file. [default: try env var LAUNCHPAD_CFG, then ./LAUNCHPAD_CFG.yml]",
)
@click.option(
    "--log-config",
    "-l",
    type=click.Path(exists=True),
    help="Use this log configuration file. [default: try env var LAUNCHPAD_LOG, then ./LAUNCHPAD_LOG.yml]",
)
@pass_settings
def main(settings, log_config, config, verbose):
    """Train, test or run a config file's model."""
    # Initialize logging before any library code so that mllp can log stuff
    if log_config:
        settings.logger = logutil.init_logging(log_config, verbose=verbose)
    else:
        settings.logger = logutil.init_logging(verbose=verbose)
    settings.verbose = verbose
    settings.conf_file = config


@main.command()
@pass_settings
def train(settings):
    """Run training, store created model and metrics."""
    _, metrics = lp.train_model(settings.config)
    print(metrics)


@main.command()
@pass_settings
def retest(settings):
    """Retest existing model, update metrics."""
    metrics = lp.retest(settings.config)
    print(metrics)


@main.command()
@pass_settings
def api(settings):
    """Run API server in unsafe debug mode."""
    settings.logger.warning(
        "Starting Flask debug server. In production, please "
        "use a WSGI server, e.g.\n"
        "'export LAUNCHPAD_CFG=addition_cfg.yml'\n"
        "'gunicorn -w 4 -b 127.0.0.1:5000 mllaunchpad.wsgi:application'"
    )
    app = Flask(__name__, root_path=settings.config["api"].get("root_path"))
    ModelApi(settings.config, app)
    # Flask apps must not be run in debug mode in production, because this allows for arbitrary code execution.
    # We know that and advise the user that this is only for debugging, so this is not a security issue (marked nosec):
    app.run(debug=True)  # nosec


@main.command()
@click.argument("json-file", type=click.File("r"))
@pass_settings
def predict(settings, json_file):
    """Run prediction on features from JSON file ( - for stdin).

    \b
    Example JSON: { "petal.width": 1.4, "petal.length": 2.0,
                    "sepal.width": 1.8, "sepal.length": 4.0 }
    """
    arg_dict = json.load(json_file)
    output = lp.predict(settings.config, arg_dict=arg_dict)
    print(output)


@main.command(name="generate-raml")
@click.argument("datasource-name", type=str, required=True)
@pass_settings
def cli_generate_raml(settings, datasource_name):
    """Generate and print RAML template from DATASOURCE_NAME.

    The datasource named DATASOURCE_NAME in the config will be used
    to create the API's query parameters (from columns), types, and examples.
    """
    print(generate_raml(settings.config, data_source_name=datasource_name))


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
