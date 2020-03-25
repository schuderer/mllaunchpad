"""Tests for `mllaunchpad.wsgi` module."""

# Stdlib imports
from importlib import reload
from unittest.mock import patch

# Third-party imports
import pytest


@patch("mllaunchpad.config.get_validated_config")
def test_log_error_on_config_filenotfound(mock_get_cfg, caplog):
    """Test that a FileNotFoundError on loading the config does
    not cause an exception, but only log a 'not found, will fail' error.
    """
    mock_get_cfg.side_effect = FileNotFoundError

    # This import is just to make sure the 'wsgi' symbol is known.
    # We will ignore what happens and afterwards reload (re-import).
    try:
        import mllaunchpad.wsgi as wsgi  # pylint: disable=unused-import
    except FileNotFoundError:
        pass
    # The proper "import" test:
    reload(wsgi)
    assert "will fail".lower() in caplog.text.lower()


@patch("mllaunchpad.api.ModelApi")
@patch("mllaunchpad.config.get_validated_config")
def test_regression_61_misleading(mock_get_cfg, mock_get_api, caplog):
    """Test that a FileNotFoundError on loading the Model does
    cause a proper exception and not merely log a 'config not found' error.
    https://github.com/schuderer/mllaunchpad/issues/61
    """
    mock_get_cfg.return_value = {"api": {}}
    mock_get_api.side_effect = FileNotFoundError

    # This import is just to make sure the 'wsgi' symbol is known.
    # We will ignore what happens and afterwards reload (re-import).
    try:
        import mllaunchpad.wsgi as wsgi  # pylint: disable=unused-import
    except FileNotFoundError:
        pass
    # The proper "import" test:
    with pytest.raises(FileNotFoundError):
        reload(wsgi)
        assert "will fail".lower() not in caplog.text.lower()
    assert mock_get_cfg.called
