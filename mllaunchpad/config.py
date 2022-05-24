"""This module contains functionality for reading and validating the
   configuration.
"""

# Stdlib imports
import logging
import os
from typing import AnyStr, Dict, TextIO, Union

# Third-party imports
import yaml  # https://camel.readthedocs.io/en/latest/yamlref.html

# Project imports
from mllaunchpad.yaml_loader import SafeIncludeLoader


logger = logging.getLogger(__name__)

CONFIG_DEFAULT = "./LAUNCHPAD_CFG.yml"
CONFIG_ENV = os.environ.get("LAUNCHPAD_CFG", CONFIG_DEFAULT)
required_config: Dict[str, Dict] = {
    # datasources and datasinks are optional
    "model_store": {"location": {}},
    "model": {
        "name": {},
        "version": {},
        "module": {},
        # custom model keys are optional
    },
    # api: is optional because using mllaunchpad's WSGI/Flask API is optional
    # (e.g. when using mllaunchpad's convenience functions in creating Azure functions).
    # You are free to add more custom settings in the config file. For an example, see
    # https://github.com/schuderer/mllaunchpad-template
}


def validate_config(config_dict, required, path=""):
    for item in required:
        path_start = (path + ":") if path else ""
        if item not in config_dict:
            raise ValueError(
                "Missing key in config file: {}".format(path_start + item)
            )
        validate_config(config_dict[item], required[item], path_start + item)


def check_semantics(config_dict):
    if "api" in config_dict and "version" in config_dict["api"]:
        raise ValueError(
            "'api:version:' is not allowed in the config, "
            "only 'model:version:'."
        )


def get_validated_config(filename: str = CONFIG_ENV) -> dict:
    """Read the configuration from file and return it as a dict object.

    :param filename: Path to configuration file
    :type filename: optional str, default: environment variable LAUNCHPAD_CFG or file ./LAUNCHPAD_CFG.yml

    :return: dict with configuration
    :rtype: dict
    """
    if filename == CONFIG_DEFAULT:
        logger.warning(
            "Config filename environment variable LAUNCHPAD_CFG not set, "
            "using default file: %s",
            repr(CONFIG_DEFAULT),
        )
    logger.info("Loading configuration file %s...", filename)

    with open(filename, encoding="utf-8") as f:
        return get_validated_config_str(f)


def get_validated_config_str(io: Union[AnyStr, TextIO]) -> dict:
    """Read the configuration from a string or open file and return it as a dict object.
    This function exists mainly for making debugging and unit testing your model's code easier.

    :param io: Configuration as unicode string or b"byte string" or a open text file to read from
    :type io: str or open text file handle

    :return: configuration
    :rtype: dict
    """
    # Normally, one should use safe_load(), but our Loader
    # is a subclass of yaml.SafeLoader
    y = yaml.load(io, SafeIncludeLoader)  # nosec

    validate_config(y, required_config)
    check_semantics(y)

    logger.debug("Configuration loaded and validated: %s", y)

    return y
