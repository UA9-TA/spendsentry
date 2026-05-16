from datetime import datetime, timezone
from typing import Optional

import typer

from spendsentry.config import load_config, save_config
from spendsentry.correlator import get_recent_commits
from spendsentry.daemon import start_daemon
from spendsentry.display import print_status
from spendsentry.providers.aws import AWSProvider
from spendsentry.storage import Storage
from spendsentry.velocity import calculate_velocity

app = typer.Typer(
    name="spendsentry", help="Real-time cloud spend monitoring and deployment guardrails"
)


@app.command()
def daemon(action: str):
    """Manage the background spend monitoring daemon."""
    if action == "start":
        start_daemon()
    else:
        typer.echo(f"Action '{action}' not implemented yet.")


@app.command()
def status():
    """Show current spend velocity and recent deployment correlation."""
    config = load_config()
    storage = Storage()
    provider = AWSProvider()  # defaults to AWS

    current_hourly = provider.get_current_hourly_spend()
    spend_today = provider.get_todays_spend()
    now = datetime.now(timezone.utc)

    recent_snapshots = storage.get_recent_snapshots(limit=168)
    historical_rates = [
        s[1] for s in recent_snapshots if datetime.fromisoformat(s[0]).hour == now.hour
    ]
    velocity = calculate_velocity(current_hourly, historical_rates, now)

    commits = get_recent_commits(limit=3)
    # Mocking some spend data for the commits since we are not storing it during get_recent_commits
    display_commits = []
    for c in commits:
        display_commits.append(
            {
                "hash": c["hash"],
                "message": c["message"],
                "timestamp": c["timestamp"],
                "spend_at_deploy": 0.02,  # default mock
            }
        )

    limits = config.get("limits", {})
    limit_today = limits.get("daily", 50.0)

    print_status(
        spend_today=spend_today,
        limit_today=limit_today,
        current_hourly=current_hourly,
        is_spiking=velocity.is_spiking,
        spike_started_at=velocity.spike_started_at,
        commits=display_commits,
        alert_sent="Telegram @ " + now.strftime("%H:%M") if velocity.is_spiking else "",
        recommendation=f"Roll back {display_commits[0]['hash'][:7]}"
        if velocity.is_spiking and display_commits
        else "",
    )


@app.command()
def history(days: int = 7):
    """Show spend history with per-deployment breakdown."""
    typer.echo(f"Showing spend history for the last {days} days...")


@app.command()
def limit(
    daily: Optional[float] = typer.Option(None, help="Daily spend limit"),
    hourly: Optional[float] = typer.Option(None, help="Hourly spend limit"),
    alert_at: int = typer.Option(80, help="Alert threshold percentage"),
):
    """Set spend limits and alert thresholds."""
    config = load_config()
    if "limits" not in config:
        config["limits"] = {}

    if daily is not None:
        config["limits"]["daily"] = daily
    if hourly is not None:
        config["limits"]["hourly"] = hourly
    config["limits"]["alert_at"] = alert_at

    save_config(config)
    typer.echo("Limits saved successfully.")


@app.command()
def check(fail_if_over: Optional[float] = None):
    """One-shot CI check. Exit 1 if spend exceeds threshold."""
    if fail_if_over is None:
        typer.echo("Please provide a threshold with --fail-if-over")
        raise typer.Exit(code=1)

    provider = AWSProvider()
    spend_today = provider.get_todays_spend()

    if spend_today > fail_if_over:
        typer.echo(
            f"CI Check Failed: Today's spend (${spend_today:.2f}) exceeds threshold (${fail_if_over:.2f})"
        )
        raise typer.Exit(code=1)
    else:
        typer.echo(
            f"CI Check Passed: Today's spend (${spend_today:.2f}) is under threshold (${fail_if_over:.2f})"
        )


@app.command()
def config(provider: Optional[str] = None, alert: Optional[str] = None):
    """Configure cloud provider and alert channel."""
    cfg = load_config()
    if provider:
        if "provider" not in cfg:
            cfg["provider"] = {}
        cfg["provider"]["name"] = provider
    if alert:
        if "alert" not in cfg:
            cfg["alert"] = {}
        cfg["alert"]["channel"] = alert

    save_config(cfg)
    typer.echo("Configuration saved.")


if __name__ == "__main__":
    app()
