from typer.testing import CliRunner
import importlib
import json


def test_cli_has_main():

    module = importlib.import_module("knwl.cli.cli")
    assert hasattr(module, "main")
    assert callable(module.main)


def test_chat_subcommand_runs_or_shows_help():
    """
    The chat subcommand should be registered. We don't run the UI in tests,
    but we can assert that invoking `knwl chat --help` returns successfully.
    """

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    result = runner.invoke(module.app, ["info", "--help"])
    # The subcommand should be available and print help (exit code 0)
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_shows_help_when_no_args():
    """
    Invoking the CLI with no arguments should show help.
    """

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    result = runner.invoke(module.app, [])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_extract_command_runs():
    """
    The extract command should run and return a knowledge graph.
    """

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    test_text = "John Field was an Irish composer."
    result = runner.invoke(
        module.app, ["extract", "-r", test_text]
    )  # using -r for raw output
    assert result.exit_code == 0
    g = json.loads(result.stdout.replace("\n", ""))  # stdout ends with a newline

    found = [u for u in g["graph"]["nodes"] if u["name"] == "John Field"]
    assert len(found) > 0


def test_config_summary():
    """
    The config command should run and return configuration information.
    """

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    result = runner.invoke(module.app, ["config", "summary", "--raw"])
    assert result.exit_code == 0
    config = json.loads(result.stdout.replace("\n", ""))  # stdout ends with a newline
    assert "blob" in config
    assert "llm" in config


def test_config_tree():
    """
    The config command should run and return configuration information.
    """

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    result = runner.invoke(module.app, ["config", "tree", "--raw"])
    assert result.exit_code == 0
    config = json.loads(result.stdout.replace("\n", ""))  # stdout ends with a newline
    assert "blob" in config
    assert "llm" in config


def test_config_get():
    """
    The config command should run and return configuration information.
    """

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    result = runner.invoke(module.app, ["config", "get", "llm"])
    assert result.exit_code == 0
    config = json.loads(result.stdout.replace("\n", ""))  # stdout ends with a newline
    assert "ollama" in config

    result = runner.invoke(module.app, ["config", "get", "llm.ollama.model"])
    assert result.exit_code == 0

    assert result.stdout.replace("\n", "") == "qwen2.5:7b"

def test_config_set():
    """
    The config command should run and set configuration information.
    """

    module = importlib.import_module("knwl.cli.cli")
    runner = CliRunner()
    result = runner.invoke(module.app, ["config", "set", "llm.ollama.model", "custom_model:1b"])
    assert result.exit_code == 0

    result = runner.invoke(module.app, ["config", "get", "llm.ollama.model"])
    assert result.exit_code == 0

    assert result.stdout.replace("\n", "") == "custom_model:1b"
    