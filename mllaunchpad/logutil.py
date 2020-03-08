# Stdlib imports
import logging
import logging.config
import os
import warnings

# Third-party imports
import yaml


LOG_CONF_FILENAME_DEFAULT = ""
LOG_CONF_FILENAME_ENV = os.environ.get(
    "LAUNCHPAD_LOG", LOG_CONF_FILENAME_DEFAULT
)


def init_logging(filename=LOG_CONF_FILENAME_ENV):
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
    if filename == "":
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            level=logging.DEBUG,
        )
    else:
        logging_config = yaml.safe_load(open(filename))
        logging.config.dictConfig(logging_config)

    logging.captureWarnings(True)
    new_logger = logging.getLogger(__name__)

    if filename == "":
        new_logger.warning(
            "Logging filename environment variable LAUNCHPAD_LOG not set,"
            + "using default logging configuration"
        )

    return new_logger
