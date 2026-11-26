import pytest
from click.testing import CliRunner

from ce.commands.registry import registry_group


def test_commands_forward_arguments(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "ce.commands.registry_downloads.execute",
        lambda *a, **kw: calls.append((a[1:], kw)),
    )
    runner = CliRunner()
    for args in (
        ["show", "--version", "2026-11-25"],
        [
            "get",
            "--class-name",
            "full",
            "--version",
            "latest",
            "--target-location",
            str(tmp_path),
        ],
        ["search", "show", "job"],
        [
            "search",
            "get",
            "--url",
            "https://api.example/exports/files/n/a.zip",
            "--target-location",
            str(tmp_path),
        ],
    ):
        result = runner.invoke(registry_group, ["downloads", *args])
        assert result.exit_code == 0, result.output
    assert calls[0] == (("show", "2026-11-25"), {})
    assert calls[1][1]["target_location"] == tmp_path
    assert calls[-1][1]["target_location"] == tmp_path
    assert calls[-1][1]["search"] is True
    assert calls[-1][0] == ("get", None)


@pytest.mark.parametrize("command", ["show", "get"])
def test_registry_version_option(monkeypatch, command):
    calls = []
    monkeypatch.setattr(
        "ce.commands.registry_downloads.execute", lambda *a, **kw: calls.append(a[1:])
    )
    runner = CliRunner()
    for args, expected in [([], "latest"), (["--version", "2026-11-25"], "2026-11-25")]:
        result = runner.invoke(
            registry_group,
            [
                "downloads",
                command,
                *(["--class-name", "full"] if command == "get" else []),
                *args,
            ],
        )
        assert result.exit_code == 0, result.output
        assert calls[-1] == (command, expected)
    result = runner.invoke(registry_group, ["downloads", command, "latest"])
    assert result.exit_code == 2


def test_unsupported_registry_list_is_not_registered():
    runner = CliRunner()
    result = runner.invoke(registry_group, ["downloads", "--help"])
    assert result.exit_code == 0
    assert "list" not in registry_group.commands["downloads"].commands
    result = runner.invoke(registry_group, ["downloads", "list"])
    assert result.exit_code == 2
    assert "No such command" in result.output
    assert (
        "list" not in registry_group.commands["downloads"].commands["search"].commands
    )
    assert (
        runner.invoke(registry_group, ["downloads", "search", "list", "job"]).exit_code
        == 2
    )


def test_target_location_default(monkeypatch):
    from pathlib import Path

    calls = []
    monkeypatch.setattr(
        "ce.commands.registry_downloads.execute", lambda *a, **kw: calls.append(kw)
    )
    runner = CliRunner()
    for args in (
        ["get", "--class-name", "full"],
        ["search", "get", "--url", "https://api.example/exports/files/n/a.zip"],
    ):
        result = runner.invoke(registry_group, ["downloads", *args])
        assert result.exit_code == 0, result.output
        assert calls[-1]["target_location"] == Path(".")


def test_get_requires_explicit_selection(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "ce.commands.registry_downloads.execute", lambda *a, **kw: calls.append(kw)
    )
    runner = CliRunner()
    for args in (
        ["get"],
        ["get", "--url", "x", "--class-name", "full"],
        ["search", "get"],
        ["search", "get", "job", "--url", "x"],
    ):
        assert runner.invoke(registry_group, ["downloads", *args]).exit_code == 2
    assert not calls
    result = runner.invoke(
        registry_group, ["downloads", "get", "--url", "a", "--url", "b"]
    )
    assert result.exit_code == 0
    assert calls[-1]["urls"] == ("a", "b")
