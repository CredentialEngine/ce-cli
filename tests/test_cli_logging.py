from inspect import signature

import click
from click.testing import CliRunner

from ce import __version__
from ce.utils.cli_logging import VersionedGroup


def separate_runner():
    return CliRunner(
        **(
            {"mix_stderr": False}
            if "mix_stderr" in signature(CliRunner).parameters
            else {}
        )
    )


def test_version_banner_and_leaf_version():
    @click.group(cls=VersionedGroup)
    @click.version_option(__version__, prog_name="ce")
    def root():
        pass

    @root.command()
    @click.option("--version", default="latest")
    def show(version):
        click.echo(version)

    runner = separate_runner()
    result = runner.invoke(root, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == f"ce, version {__version__}\n"
    assert not result.stderr
    result = runner.invoke(root, ["show", "--version", "2026-11-25"])
    assert result.exit_code == 0
    assert result.stdout == "2026-11-25\n"
    assert result.stderr == f"ce, version {__version__}\n"
    assert runner.invoke(root, ["show", "--log-level", "DEBUG"]).exit_code == 2
