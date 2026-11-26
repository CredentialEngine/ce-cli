from click.testing import CliRunner


def test_persistent_logging(tmp_path, monkeypatch):
    from ce.commands.logging import logging_group
    from ce.config import context

    monkeypatch.setattr(context, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(context, "ensure_config_dir", lambda: None)
    runner = CliRunner()
    assert runner.invoke(logging_group, ["show"]).output.strip() == "WARNING"
    assert runner.invoke(logging_group, ["set", "log-level", "debug"]).exit_code == 0
    assert context.load_cli_config().log_level == "DEBUG"
    assert runner.invoke(logging_group, ["show"]).output.strip() == "DEBUG"
    assert runner.invoke(logging_group, ["set", "log-level", "TRACE"]).exit_code == 2
