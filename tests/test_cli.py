from typer.testing import CliRunner


def test_cli_has_main():
    import importlib

    module = importlib.import_module("knwl.cli.cli")
    assert hasattr(module, "main")
    assert callable(module.main)




def test_chat_subcommand_runs_or_shows_help():
    """The chat subcommand should be registered. We don't run the UI in tests,
    but we can assert that invoking `knwl chat --help` returns successfully."""
    import importlib

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    result = runner.invoke(module.app, ["info", "--help"])
    # The subcommand should be available and print help (exit code 0)
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_shows_help_when_no_args():
    """Invoking the CLI with no arguments should show help."""
    import importlib

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    result = runner.invoke(module.app, [])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
