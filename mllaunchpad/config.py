# -*- coding: utf-8 -*-

"""This module contains functionality for reading and validating the
   configuration.
"""

# Stdlib imports
import logging
import os

# Third-party imports
import yaml  # https://camel.readthedocs.io/en/latest/yamlref.html

logger = logging.getLogger(__name__)

CONFIG_DEFAULT = "./mllaunchpad.yml"
CONFIG_ENV = os.environ.get("LAUNCHPAD_CFG", CONFIG_DEFAULT)


def get_validated_config(filename=CONFIG_ENV):
    """Read the configuration from file and return it as a dict object.

    Validation is not done yet and planned when the configuration is more
    stable.

    Params:
        - filename: path to configuration file
                    (default: environment variable LAUNCHPAD_CFG)

    Returns:
        dict with configuration
    """
    if filename == CONFIG_DEFAULT:
        logger.warning(
            "Config filename environment variable LAUNCHPAD_CFG not set, "
            "using default: %s",
            repr(CONFIG_DEFAULT),
        )
    logger.info("Loading configuration file %s...", filename)

    with open(filename) as f:
        y = yaml.safe_load(f)

    req_props = ["model", "api"]

    for prop in req_props:
        if prop not in y:
            raise ValueError(
                "Configuration file {} does not contain {} property.".format(
                    filename, prop
                )
            )

    # TODO: should completely validate config structure when stable

    logger.debug("Configuration loaded and validated: %s", y)

    return y
