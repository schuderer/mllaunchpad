import os
import yaml  # https://camel.readthedocs.io/en/latest/yamlref.html
import logging

logger = logging.getLogger(__name__)

CONFIG_DEFAULT = './config_EXAMPLE.yml'
CONFIG_ENV = os.environ.get('LAUNCHPAD_CFG', CONFIG_DEFAULT)


def get_validated_config(filename=CONFIG_ENV):
    if filename == CONFIG_DEFAULT:
        logger.warning('Config filename environment variable LAUNCHPAD_CFG not set, using default: %s', repr(CONFIG_DEFAULT))
    logger.info('Loading configuration file %s...', filename)

    with open(filename) as f:
        y = yaml.safe_load(f)

    req_props = ['model', 'api']

    for prop in req_props:
        if prop not in y:
            raise ValueError('Configuration file {} does not contain {} property.'
                             .format(filename, prop))

    # TODO: should completely validate config structure when stable

    logger.debug('Configuration loaded and validated: %s', y)

    return y
