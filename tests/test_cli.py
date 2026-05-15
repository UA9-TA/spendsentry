from datetime import datetime

from typer.testing import CliRunner

from spendsentry.cli import app
from spendsentry.config import get_config

runner = CliRunner()


def test_cli_config(tmp_path, monkeypatch):
    monkeypatch.setattr("spendsentry.config.CONFIG_FILE", tmp_path / "config.toml")
    result = runner.invoke(app, ["config", "--provider", "aws", "--alert", "telegram"])
    assert result.exit_code == 0
    assert "Cloud provider set to aws" in result.stdout
    assert "Alert channel set to telegram" in result.stdout

    config = get_config()
    assert config["cloud"]["provider"] == "aws"
    assert config["alerts"]["channel"] == "telegram"


def test_cli_limit(tmp_path, monkeypatch):
    monkeypatch.setattr("spendsentry.config.CONFIG_FILE", tmp_path / "config.toml")
    result = runner.invoke(app, ["limit", "--daily", "50", "--hourly", "5", "--alert-at", "80"])
    assert result.exit_code == 0
    assert "Limits updated successfully" in result.stdout

    config = get_config()
    assert config["limits"]["daily"] == 50.0
    assert config["limits"]["hourly"] == 5.0
    assert config["limits"]["alert_at"] == 80


def test_cli_check_success(tmp_path, monkeypatch):
    monkeypatch.setattr("spendsentry.config.CONFIG_FILE", tmp_path / "config.toml")

    # Mocking AWSSpendProvider
    class MockProvider:
        def get_current_spend(self):
            class SpendData:
                daily_cost = 5.0
                hourly_cost = 1.0
                timestamp = datetime.now()

            return SpendData()

    monkeypatch.setattr("spendsentry.cli.AWSSpendProvider", MockProvider)

    result = runner.invoke(app, ["check", "--fail-if-over", "10"])
    assert result.exit_code == 0
    assert "SUCCESS" in result.stdout


def test_cli_check_fail(tmp_path, monkeypatch):
    monkeypatch.setattr("spendsentry.config.CONFIG_FILE", tmp_path / "config.toml")

    class MockProvider:
        def get_current_spend(self):
            class SpendData:
                daily_cost = 15.0
                hourly_cost = 1.0
                timestamp = datetime.now()

            return SpendData()

    monkeypatch.setattr("spendsentry.cli.AWSSpendProvider", MockProvider)

    result = runner.invoke(app, ["check", "--fail-if-over", "10"])
    assert result.exit_code == 1
    assert "ERROR" in result.stdout


def test_cli_status(tmp_path, monkeypatch, mocker):
    monkeypatch.setattr("spendsentry.config.CONFIG_FILE", tmp_path / "config.toml")

    class MockProvider:
        def get_current_spend(self):
            class SpendData:
                daily_cost = 4.21
                hourly_cost = 1.83
                timestamp = datetime.now()

            return SpendData()

    monkeypatch.setattr("spendsentry.cli.AWSSpendProvider", MockProvider)

    mocker.patch(
        "spendsentry.cli.get_recent_snapshots",
        return_value=[
            {
                "timestamp": datetime.now().isoformat(),
                "hourly_cost": "1.83",
                "daily_cost": "4.21",
                "provider": "aws",
            }
        ],
    )

    mocker.patch(
        "spendsentry.cli.get_recent_deployments",
        return_value=[
            {
                "commit_hash": "abc1234",
                "message": "feat",
                "timestamp": datetime.now(),
                "spend_at_deploy": 0.02,
            }
        ],
    )

    from spendsentry.velocity import VelocityReport

    mocker.patch(
        "spendsentry.cli.calculate_velocity",
        return_value=VelocityReport(
            current_hourly_rate=1.83,
            baseline_hourly_rate=0.5,
            acceleration_factor=3.66,
            is_spiking=True,
            spike_started_at=datetime.now(),
        ),
    )

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "SpendSentry — Spend Monitor" in result.stdout
    assert "Today's spend" in result.stdout


def test_cli_history(tmp_path, monkeypatch, mocker):
    monkeypatch.setattr("spendsentry.config.CONFIG_FILE", tmp_path / "config.toml")

    mocker.patch(
        "spendsentry.cli.get_recent_snapshots",
        return_value=[
            {
                "timestamp": datetime.now().isoformat(),
                "hourly_cost": 1.83,
                "daily_cost": 4.21,
                "provider": "aws",
            }
        ],
    )

    result = runner.invoke(app, ["history", "--days", "1"])
    assert result.exit_code == 0
    assert "Spend history" in result.stdout
    assert "1.83" in result.stdout
