import os
import yaml
import logging
import logging.config


LOG_CONF_FILENAME_DEFAULT = './logging_cfg.yml'
LOG_CONF_FILENAME_ENV = os.environ.get('LAUNCHPAD_LOG', LOG_CONF_FILENAME_DEFAULT)


def init_logging(filename=LOG_CONF_FILENAME_ENV):
    logging_config = yaml.safe_load(open(filename))
    logging.config.dictConfig(logging_config)
    logging.captureWarnings(True)
    new_logger = logging.getLogger(__name__)
    if filename == LOG_CONF_FILENAME_DEFAULT:
        new_logger.warning('Logging filename environment variable LAUNCHPAD_LOG not set, using default: %s',
                            repr(LOG_CONF_FILENAME_DEFAULT))

    return new_logger
