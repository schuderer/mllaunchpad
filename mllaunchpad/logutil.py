# Stdlib imports
import logging
import logging.config
import os
import warnings

# Third-party imports
import yaml


LOG_CONF_FILENAME_DEFAULT = "./LAUNCHPAD_LOG.yml"
LOG_CONF_FILENAME_ENV = os.environ.get(
    "LAUNCHPAD_LOG", LOG_CONF_FILENAME_DEFAULT
)


def init_logging(filename=LOG_CONF_FILENAME_ENV, verbose=False):
    """Only called from wsgi or cli module (mllaunchpad-as-an-app).
    It's important to not change logging/warning config from the library-only
    code.
    """
    # Ignore all deprecation warnings:
    warnings.filterwarnings(action="ignore", category=DeprecationWarning)
    # Except from mllaunchpad itself:
    warnings.filterwarnings(
        action="default", category=DeprecationWarning, module="mllaunchpad.*"
    )
    try:
        with open(filename, encoding="utf-8") as file:
            loaded_logging_config = yaml.safe_load(file)
            logging.config.dictConfig(loaded_logging_config)
    except FileNotFoundError:
        loaded_logging_config = None
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            level=logging.DEBUG if verbose else logging.INFO,
        )

    logging.captureWarnings(True)
    new_logger = logging.getLogger(__name__)
    if verbose:
        new_logger.setLevel(logging.DEBUG)

    if not loaded_logging_config:
        new_logger.warning(
            "Logging filename environment variable LAUNCHPAD_LOG not set, "
            "and ./LAUNCHPAD_LOG.yml not found: using default logging "
            "configuration"
        )
    elif filename == LOG_CONF_FILENAME_DEFAULT:
        new_logger.warning(
            "Logging filename environment variable LAUNCHPAD_LOG not set, "
            "using default logging configuration file ./LAUNCHPAD_LOG.yml"
        )

    return new_logger
