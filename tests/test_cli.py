"""Tests for `mllaunchpad.cli` module."""

# Stdlib imports
from unittest import mock

# Third-party imports
import pytest
from click.testing import CliRunner

# Project imports
import mllaunchpad.cli as cli


@pytest.yield_fixture()
def runner_cfg_logcfg():
    """Click runner with config and log config file"""
    cfg_file = "test_cfg.yml"
    log_cfg_file = "log_cfg.yml"
    r = CliRunner(mix_stderr=False)
    with r.isolated_filesystem():
        with open(cfg_file, "w") as f:
            f.write("my: config")
        with open(log_cfg_file, "w") as f:
            f.write("my: log config")
        yield r, cfg_file, log_cfg_file


def test_dunder_main():
    import mllaunchpad.__main__  # noqa: F401


def test_no_command():
    """Test the Command Line Interface without any arguments."""
    runner = CliRunner()
    result = runner.invoke(cli.main, [])
    print(result.output)
    assert result.exit_code == 0


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    print(result.output)
    assert result.exit_code == 0
    assert "Show this message" in result.output


@mock.patch("{}.logutil.init_logging".format(cli.__name__))
@mock.patch(
    "{}.mllp.train_model".format(cli.__name__), return_value=("", "my_metrics")
)
@mock.patch(
    "{}.mllp.get_validated_config".format(cli.__name__),
    return_value="my_config",
)
def test_train_cfg_log_config_verbose(
    get_cfg, train, init_logging_mock, runner_cfg_logcfg
):
    """Test the Command Line Interface's train command + options log-config and verbose."""
    runner, cfg, log_conf = runner_cfg_logcfg

    # Test Train + Config
    result = runner.invoke(cli.main, ["--config", cfg, "train"])
    print(result.output)
    assert result.exit_code == 0
    train.assert_called_with("my_config")
    assert "my_metrics" in result.output

    # Log-config
    result = runner.invoke(cli.main, ["--log-config", log_conf, "train"])
    print(result.output)
    assert result.exit_code == 0
    init_logging_mock.assert_called_with(log_conf, verbose=False)

    # Verbose
    result = runner.invoke(cli.main, ["--verbose", "train"])
    print(result.output)
    assert result.exit_code == 0
    init_logging_mock.assert_called_with(verbose=True)


@mock.patch(
    "{}.mllp.retest".format(cli.__name__), return_value=("", "my_metrics")
)
@mock.patch(
    "{}.mllp.get_validated_config".format(cli.__name__),
    return_value="my_config",
)
def test_retest(get_cfg, retest, runner_cfg_logcfg):
    """Test the retest command."""
    runner, cfg, _ = runner_cfg_logcfg

    result = runner.invoke(cli.main, ["--config", cfg, "retest"])
    print(result.output)
    assert result.exit_code == 0
    retest.assert_called_with("my_config")
    assert "my_metrics" in result.output


@mock.patch("{}.Settings.config".format(cli.__name__))
@mock.patch("{}.Flask".format(cli.__name__))
@mock.patch("{}.ModelApi".format(cli.__name__))
def test_api(ma, flask, config, runner_cfg_logcfg, caplog):
    """Test the CLI api startup."""
    runner, cfg, _ = runner_cfg_logcfg
    app = mock.Mock()
    flask.return_value = app

    result = runner.invoke(cli.main, ["--config", cfg, "api"])
    print(result.output)
    assert result.exit_code == 0
    assert (
        "production".lower() in caplog.text.lower()
    )  # Non-production Flask server warning
    flask.assert_called()
    ma.assert_called_with(config, app, debug=True)
    app.run.assert_called()


@mock.patch(
    "{}.mllp.predict".format(cli.__name__), return_value=("", "my_metrics")
)
@mock.patch("{}.Settings.config".format(cli.__name__))
def test_predict(config, predict, runner_cfg_logcfg):
    """Test the predict function."""
    runner, cfg, _ = runner_cfg_logcfg
    predict.return_value = "my_prediction"

    j_file = "test_387213.json"
    j_contents = {"a": 3}
    with open(j_file, "w") as j:
        # We're still using Click's isolated file system context
        j.write('{"a": 3}')

    result = runner.invoke(
        cli.main, ["--config", cfg, "pred", j_file]
    )  # abbreviated on purpose to test short commands
    print(result.output)
    assert result.exit_code == 0
    predict.assert_called_with(config, arg_dict=j_contents, use_live_code=True)
    assert "my_prediction" in result.output


@mock.patch("{}.generate_raml".format(cli.__name__), return_value="my_raml")
@mock.patch("{}.Settings.config".format(cli.__name__))
def test_generate_raml(config, raml, runner_cfg_logcfg):
    """Test the RAML generation from CLI."""
    runner, cfg, _ = runner_cfg_logcfg

    result = runner.invoke(
        cli.main, ["--config", cfg, "gen", "some_data_source"]
    )  # abbreviated on purpose to test short commands
    print("stdout='" + result.stdout.strip() + "'")
    # print("stderr='"+result.stderr.strip()+"'")
    assert result.exit_code == 0
    raml.assert_called()
    assert result.stdout.strip() == "my_raml"
