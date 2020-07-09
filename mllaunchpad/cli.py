"""This module provides the command line interface for ML Launchpad"""

# Stdlib imports
import json
import sys
from logging import Logger
from typing import Dict

# Third-party imports
import click
from flask import Flask

# Project imports
import mllaunchpad as mllp
from mllaunchpad import logutil
from mllaunchpad.api import ModelApi, generate_raml


# Fix for click using the wrong name if run using `python -m mllaunchpad`
# Also see: https://github.com/pallets/click/issues/365
sys.argv[0] = mllp.__name__


# Adapted from https://click.palletsprojects.com/en/7.x/advanced/
class AliasedGroup(click.Group):
    """Commands can be abbreviated, e.g. t or tr for train, a for api, etc."""

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [
            x for x in self.list_commands(ctx) if x.startswith(cmd_name)
        ]
        if not matches:
            return None
        elif len(matches) == 1:
            click.echo(
                "Command {} matches {}".format(cmd_name, matches[0]), err=True
            )
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(
            "Command {} is ambiguous: {}".format(
                cmd_name, ", ".join(sorted(matches))
            )
        )


# TODO: Migrate to @dataclass when dropping support for Python 3.6
class Settings:
    def __init__(self):
        self.verbose: bool = False
        self.logger: Logger = None
        self.conf_file: str = None
        self._config: Dict = None

    @property
    def config(self):
        if not hasattr(self, "_config") or not self._config:
            if self.conf_file:
                self._config = mllp.get_validated_config(self.conf_file)
            else:
                self._config = mllp.get_validated_config()
        return self._config


pass_settings = click.make_pass_decorator(Settings, ensure=True)


@click.group(
    cls=AliasedGroup, context_settings=dict(help_option_names=["-h", "--help"])
)
@click.version_option(prog_name="ML Launchpad")
@click.option("--verbose", "-v", is_flag=True, help="Print debug messages.")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Use this configuration file. [default: look for env var LAUNCHPAD_CFG or ./LAUNCHPAD_CFG.yml]",
)
@click.option(
    "--log-config",
    "-l",
    type=click.Path(exists=True),
    help="Use this log configuration file. [default: look for env var LAUNCHPAD_LOG or ./LAUNCHPAD_LOG.yml]",
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
    _, metrics = mllp.train_model(settings.config)
    print(metrics)


@main.command()
@pass_settings
def retest(settings):
    """Retest existing model, update metrics."""
    metrics = mllp.retest(settings.config)
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
    ModelApi(settings.config, app, debug=True)
    # Flask apps must not be run in debug mode in production, because this allows for arbitrary code execution.
    # We know that and advise the user that this is only for debugging, so this is not a security issue (marked nosec):
    app.run(debug=True)  # nosec


@main.command()
@click.argument("json-file", type=click.File("r"), default=sys.stdin)
@pass_settings
def predict(settings, json_file):
    """Run prediction on features from JSON file ( - for stdin).

    \b
    Example JSON: { "petal.width": 1.4, "petal.length": 2.0,
                    "sepal.width": 1.8, "sepal.length": 4.0 }
    """
    arg_dict = json.load(json_file)
    output = mllp.predict(
        settings.config, arg_dict=arg_dict, use_live_code=True
    )
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
    # PyLint (used by Codacity) does not know that the signature of `main()`
    # is being changed by Click at runtime. Disable the warning.
    sys.exit(
        main()  # pylint: disable=no-value-for-parameter; # pragma: no cover
    )
