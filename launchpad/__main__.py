import getopt
import sys
from flask import Flask
from .model_actions import train_model, retest, predict
from .config import get_validated_config
from .api import generate_raml
from .api import ModelApi
from . import logutil

HELP_STRING = '''
Parameters:
-h          / --help                  : Print this help
-t          / --train                 : Run training, store model and metrics
-r          / --retest                : Retest model, update metrics
-a          / --api                   : Run API Server (Debug Mode!)
-c <file>   / --config=<file>         : Config file to use
-l <file>   / --logconfig=<file>      : Log config file to use
-g <datsrc> / --generateraml=<datsrc> : Generate and print RAML template from data source name
'''


def main():
    fullCmdArguments = sys.argv
    argumentList = fullCmdArguments[1:]
    unixOptions = 'htrpac:l:g:'
    gnuOptions = ['help', 'train', 'retest', 'predict' 'api', 'config=', 'logconfig=', 'generateraml=']
    try:
        arguments, values = getopt.getopt(argumentList, unixOptions, gnuOptions)
    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))
        sys.exit(2)
    # evaluate given options
    cmd = None
    conf = None
    logger = None
    raml_ds = None
    for currentArgument, currentValue in arguments:
        if currentArgument in ('-c', '--config'):
            conf = get_validated_config(currentValue)
        elif currentArgument in ('-l', '--logconfig'):
            logger = logutil.init_logging(currentValue)
        elif currentArgument in ('-t', '--train'):
            cmd = 'train'
        elif currentArgument in ('-r', '--retest'):
            cmd = 'retest'
        elif currentArgument in ('-p', '--predict'):
            cmd = 'predict'
        elif currentArgument in ('-a', '--api'):
            cmd = 'api'
        elif currentArgument in ('-g', '--generateraml'):
            cmd = 'genraml'
            raml_ds = currentValue
        elif currentArgument in ('-h', '--help'):
            print(HELP_STRING)
            exit(0)

    if cmd is None:
        print('\nNo command given.')
        print(HELP_STRING)
        exit(1)

    logger = logger or logutil.init_logging()
    conf = conf or get_validated_config()
    if cmd == 'train':
        model, metrics = train_model(conf)
    elif cmd == 'retest':
        metrics = retest(conf)
    elif cmd == 'predict':
        output = predict(conf, arg_dict={})  # TODO decide: get batch arguments from config? Don't support arguments?
    elif cmd == 'api':
        logger.warning("Starting Flask debug server. In production, please use a WSGI server, "
                       + "e.g. 'gunicorn -w 4 -b 127.0.0.1:5000 launchpad.wsgi:app'")
        app = Flask(__name__)
        ModelApi(conf, app)
        app.run(debug=True)
    elif cmd == 'genraml':
        print(generate_raml(conf, data_source_name=raml_ds))


if __name__ == '__main__':
    main()
