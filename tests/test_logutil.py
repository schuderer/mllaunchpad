"""Tests for the mllaunchpad.logutil module"""

# Stdlib imports
from unittest import mock

# Project imports
import mllaunchpad.logutil as lu


def test_init_logging():
    _ = lu.init_logging()

    # pytest itself interferes with log level, need to find workaround
    # import logging
    # logger = logging.getLogger(__name__)
    # assert logger.level == logging.INFO


def test_init_logging_verbose():
    _ = lu.init_logging(verbose=True)

    # pytest itself interferes with log level, need to find workaround
    # import logging
    # own_logger = logging.getLogger(__name__)
    # assert own_logger.level == logging.DEBUG
    # assert logger.level == logging.DEBUG


logging_config = """
---
version: 1
disable_existing_loggers: False
formatters:
    simple:
        format: "%(asctime)s %(levelname)s %(name)s: %(message)s"

handlers:
    console:
        class: logging.StreamHandler
        level: DEBUG
        formatter: simple
        stream: ext://sys.stdout

loggers:
    my_module:
        level: DEBUG
        handlers: [console]
        propagate: no

root:
    level: DEBUG
    handlers: [console]
"""


@mock.patch("{}.logging.config.dictConfig".format(lu.__name__))
def test_init_logging_file(dc):
    mo = mock.mock_open(read_data=logging_config)
    with mock.patch("builtins.open", mo, create=True):
        _ = lu.init_logging("some_file.yml")
    mo.assert_called_once()
    dc.assert_called_once()
