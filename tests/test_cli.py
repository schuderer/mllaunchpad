#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mllaunchpad.cli` module."""

# Stdlib imports
import sys

# Third-party imports
# from click.testing import CliRunner
import pytest

# Application imports
import mllaunchpad.cli as cli


def test_command_line_interface(capsys):
    """Test the CLI."""
    with pytest.raises(SystemExit) as e:
        cli.main()
    out, err = capsys.readouterr()
    assert e.value.code == 1

    sys.argv = [sys.argv[0], "--help"]
    with pytest.raises(SystemExit) as e:
        cli.main()
    out, err = capsys.readouterr()
    assert e.value.code == 0
    assert "Print this help" in err
