import yaml  # https://camel.readthedocs.io/en/latest/yamlref.html
import logging

logger = logging.getLogger(__name__)

CONFIG_DEFAULT = "./config_EXAMPLE.yml"


def get_validated_config(filename=CONFIG_DEFAULT):
    if filename == CONFIG_DEFAULT:
        logger.warn("Config filename not set, using default: '%s'", CONFIG_DEFAULT)
    logger.info("Loading configuration file %s...", filename)

    with open(filename) as f:
        y = yaml.safe_load(f)

    req_props = ['model', 'api']

    for prop in req_props:
        if (prop not in y):
            raise ValueError("Configuration file {} does not contain {} property.".format(filename, prop))

    # TODO: should completely validate config structure when stable

    logger.debug("Configuration loaded and validated: %s", y)

    return y
