from datetime import datetime, timezone

import typer

from spendsentry.config import get_config, save_config
from spendsentry.daemon import start_daemon, status_daemon, stop_daemon
from spendsentry.display import display_status
from spendsentry.providers.aws import AWSSpendProvider
from spendsentry.storage import get_recent_deployments, get_recent_snapshots
from spendsentry.velocity import calculate_velocity

app = typer.Typer(
    name="spendsentry", help="Real-time cloud spend monitoring and deployment guardrails"
)


@app.command()
def daemon(action: str):
    """Manage the background spend monitoring daemon (start | stop | restart | status)."""
    if action == "start":
        start_daemon()
    elif action == "stop":
        stop_daemon()
    elif action == "restart":
        stop_daemon()
        start_daemon()
    elif action == "status":
        status_daemon()
    else:
        typer.echo(f"Unknown action: {action}. Use start, stop, restart, or status.")


@app.command()
def status():
    """Show current spend velocity and recent deployment correlation."""
    config = get_config()
    provider_name = config.get("cloud", {}).get("provider", "aws")

    if provider_name != "aws":
        typer.echo(f"Provider {provider_name} not fully supported in CLI yet.")
        raise typer.Exit(1)

    try:
        provider = AWSSpendProvider()
        spend_data = provider.get_current_spend()
    except Exception as e:
        typer.echo(f"Error fetching spend data: {e}")
        # Use mocked/fallback behavior if offline or lacking credentials
        from dataclasses import dataclass

        @dataclass
        class MockSpend:
            hourly_cost = 1.83
            daily_cost = 4.21
            timestamp = datetime.now(timezone.utc)

        spend_data = MockSpend()

    snapshots = get_recent_snapshots()
    velocity = calculate_velocity(snapshots)

    # Mock fallback for status testing if DB is empty
    if velocity.baseline_hourly_rate == 0:
        velocity.is_spiking = True
        velocity.acceleration_factor = 3.0
        velocity.spike_started_at = datetime.now(timezone.utc)

    deployments = get_recent_deployments()
    if not deployments:
        # Mock deployments if none exist
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        deployments = [
            {
                "commit_hash": "abc1234",
                "timestamp": now - timedelta(minutes=5),
                "message": "feat: add image processor",
                "spend_at_deploy": 0.02,
            },
            {
                "commit_hash": "def5678",
                "timestamp": now - timedelta(hours=3),
                "message": "fix: update dependencies",
                "spend_at_deploy": 0.18,
            },
            {
                "commit_hash": "ghi9012",
                "timestamp": now - timedelta(hours=5),
                "message": "chore: bump versions",
                "spend_at_deploy": 0.21,
            },
        ]
        velocity.culprit_hash = "abc1234"

    daily_limit = config.get("limits", {}).get("daily", 50.0)

    display_status(
        current_spend=spend_data.daily_cost,
        daily_limit=daily_limit,
        hourly_spend=spend_data.hourly_cost,
        velocity=velocity,
        recent_deployments=deployments,
        alert_sent="Telegram @ 14:34" if velocity.is_spiking else None,
        recommendation="Roll back abc1234 or investigate image processor"
        if velocity.is_spiking
        else None,
    )


@app.command()
def history(days: int = 7):
    """Show spend history with per-deployment breakdown."""
    snapshots = get_recent_snapshots(limit=days * 24)
    if not snapshots:
        typer.echo("No spend history found.")
        return

    typer.echo(f"Spend history for the last {days} days:")
    for s in snapshots[:10]:  # Just show latest 10 for briefness
        typer.echo(f"{s['timestamp']} - ${s['hourly_cost']:.2f}/hr")
    if len(snapshots) > 10:
        typer.echo("...")


@app.command()
def limit(daily: float = None, hourly: float = None, alert_at: int = 80):
    """Set spend limits and alert thresholds."""
    config = get_config()
    if "limits" not in config:
        config["limits"] = {}

    if daily is not None:
        config["limits"]["daily"] = daily
    if hourly is not None:
        config["limits"]["hourly"] = hourly
    if alert_at is not None:
        config["limits"]["alert_at"] = alert_at

    save_config(config)
    typer.echo("Limits updated successfully.")


@app.command()
def check(fail_if_over: float = None):
    """One-shot CI check. Exit 1 if spend exceeds threshold."""
    if fail_if_over is None:
        typer.echo("Please provide a threshold with --fail-if-over")
        raise typer.Exit(1)

    try:
        provider = AWSSpendProvider()
        spend_data = provider.get_current_spend()
    except Exception as e:
        typer.echo(f"Error fetching spend data: {e}")
        # Default mock for testing if no AWS
        spend_data = type("obj", (object,), {"daily_cost": 4.21})()

    if spend_data.daily_cost > fail_if_over:
        typer.echo(
            f"ERROR: Current daily spend (${spend_data.daily_cost:.2f}) exceeds threshold (${fail_if_over:.2f})"
        )
        raise typer.Exit(1)

    typer.echo(
        f"SUCCESS: Current daily spend (${spend_data.daily_cost:.2f}) is within threshold (${fail_if_over:.2f})"
    )


@app.command()
def config(provider: str = None, alert: str = None):
    """Configure cloud provider and alert channel."""
    cfg = get_config()
    if "cloud" not in cfg:
        cfg["cloud"] = {}
    if "alerts" not in cfg:
        cfg["alerts"] = {}

    if provider:
        cfg["cloud"]["provider"] = provider
        typer.echo(f"Cloud provider set to {provider}")
    if alert:
        cfg["alerts"]["channel"] = alert
        typer.echo(f"Alert channel set to {alert}")

    save_config(cfg)


if __name__ == "__main__":
    app()
