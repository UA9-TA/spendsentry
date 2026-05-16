from typer.testing import CliRunner

from spendsentry.cli import app

runner = CliRunner()


def test_config_command():
    result = runner.invoke(app, ["config", "--provider", "aws", "--alert", "telegram"])
    assert result.exit_code == 0
    assert "Configuration saved." in result.stdout


def test_limit_command():
    result = runner.invoke(app, ["limit", "--daily", "50", "--hourly", "5"])
    assert result.exit_code == 0
    assert "Limits saved successfully." in result.stdout


def test_history_command():
    result = runner.invoke(app, ["history", "--days", "7"])
    assert result.exit_code == 0
    assert "Showing spend history for the last 7 days..." in result.stdout
