# -*- coding: utf-8 -*-

"""This module provides the command line interface for ML Launchpad"""

# Stdlib imports
import getopt
import sys

# Third-party imports
from flask import Flask

# Application imports
import mllaunchpad as lp
from mllaunchpad import logutil
from mllaunchpad.api import generate_raml
from mllaunchpad.api import ModelApi

HELP_STRING = """
Parameters:
-h          / --help                  : Print this help
-v          / --version               : Print the version
-t          / --train                 : Run training, store model and metrics
-r          / --retest                : Retest model, update metrics
-a          / --api                   : Run API Server (Debug Mode!)
-c <file>   / --config=<file>         : Config file to use
-l <file>   / --logconfig=<file>      : Log config file to use
-g <datsrc> / --generateraml=<datsrc> : Generate and print RAML template
                                        from data source name
"""


def main():
    fullCmdArguments = sys.argv
    argumentList = fullCmdArguments[1:]
    unixOptions = "hvtrpac:l:g:"
    gnuOptions = [
        "help",
        "version",
        "train",
        "retest",
        "predict",
        "api",
        "config=",
        "logconfig=",
        "generateraml=",
    ]
    try:
        arguments, values = getopt.getopt(
            argumentList, unixOptions, gnuOptions
        )
    except getopt.error as err:
        # output error, and return with an error code
        print(str(err), file=sys.stderr)
        sys.exit(2)
    # evaluate given options
    cmd = None
    conf = None
    logger = None
    raml_ds = None
    for currentArgument, currentValue in arguments:
        if currentArgument in ("-c", "--config"):
            conf = lp.get_validated_config(currentValue)
        elif currentArgument in ("-l", "--logconfig"):
            logger = logutil.init_logging(currentValue)
        elif currentArgument in ("-t", "--train"):
            cmd = "train"
        elif currentArgument in ("-r", "--retest"):
            cmd = "retest"
        elif currentArgument in ("-p", "--predict"):
            cmd = "predict"
        elif currentArgument in ("-a", "--api"):
            cmd = "api"
        elif currentArgument in ("-g", "--generateraml"):
            cmd = "genraml"
            raml_ds = currentValue
        elif currentArgument in ("-h", "--help"):
            print(HELP_STRING, file=sys.stderr)
            exit(0)
        elif currentArgument in ("-v", "--version"):
            print("ML Launchpad version " + lp.__version__, file=sys.stderr)
            exit(0)

    if cmd is None:
        print("\nNo command given.", file=sys.stderr)
        print(HELP_STRING, file=sys.stderr)
        exit(1)

    logger = logger or logutil.init_logging()
    conf = conf or lp.get_validated_config()
    if cmd == "train":
        model, metrics = lp.train_model(conf)
    elif cmd == "retest":
        _ = lp.retest(conf)
    elif cmd == "predict":
        # TODO decide: get batch args from config? Don't support arguments?
        _ = lp.predict(conf, arg_dict={})
    elif cmd == "api":
        logger.warning(
            "Starting Flask debug server. In production, please "
            "use a WSGI server, e.g. "
            "'export LAUNCHPAD_CFG=addition_cfg.yml'"
            "'gunicorn -w 4 -b 127.0.0.1:5000 mllaunchpad.wsgi:application'"
        )
        app = Flask(__name__, root_path=conf["api"].get("root_path"))
        ModelApi(conf, app)
        app.run(debug=True)
    elif cmd == "genraml":
        print(generate_raml(conf, data_source_name=raml_ds))


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
