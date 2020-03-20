"""Tests for `mllaunchpad.model_actions` module."""

# Stdlib imports
from unittest.mock import patch

# Project imports
from mllaunchpad import model_actions as ma


@patch("mllaunchpad.model_interface.ModelInterface", autospec=True)
def test__check_ordered_columns(mock_wrapper, caplog):
    from mllaunchpad.resource import order_columns

    dummy_config = {"model": {}}

    ma._check_ordered_columns(dummy_config, mock_wrapper, "never_ordered")
    assert "never_ordered".lower() not in caplog.text.lower()

    mock_wrapper.__ordered_columns = True
    ma._check_ordered_columns(
        dummy_config, mock_wrapper, "ordered_only_in_train"
    )
    assert "ordered_only_in_train does not call".lower() in caplog.text.lower()

    order_columns({"a": 1})
    ma._check_ordered_columns(
        dummy_config, mock_wrapper, "ordered_in_train_and_now"
    )
    assert "ordered_in_train_and_now".lower() not in caplog.text.lower()
