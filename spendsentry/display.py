from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def display_status(
    current_spend,
    daily_limit,
    hourly_spend,
    velocity,
    recent_deployments,
    alert_sent=None,
    recommendation=None,
):

    status_text = Text()
    status_text.append("✦ Today's spend       ", style="bold")
    status_text.append(
        f"${current_spend:.2f}", style="green" if current_spend < daily_limit else "red"
    )
    status_text.append(f"  (limit: ${daily_limit:.2f})\n")

    status_text.append("✦ Last hour           ", style="bold")
    if velocity.is_spiking:
        status_text.append(f"${hourly_spend:.2f}", style="red bold")
        status_text.append(f"  ⚠ HIGH — {velocity.acceleration_factor:.1f}× normal rate\n")
    else:
        status_text.append(f"${hourly_spend:.2f}", style="green")
        status_text.append("  (normal)\n")

    status_text.append("✦ Spend velocity      ", style="bold")
    if velocity.is_spiking:
        status_text.append(
            f"↑ accelerating since {velocity.spike_started_at.strftime('%H:%M')}\n", style="red"
        )
    else:
        status_text.append("→ steady\n", style="green")

    status_text.append("\n  Recent deployments:\n")

    from datetime import datetime

    for dep in recent_deployments:
        # Handle sqlite3.Row strings vs mock datetime objects
        timestamp = dep["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        time_str = timestamp.strftime("%H:%M")
        hash_str = dep["commit_hash"][:7]
        msg = dep["message"]

        # Support both dictionary and sqlite3.Row access
        spend_at_deploy = 0.18
        if "spend_at_deploy" in dep.keys():
            val = dep["spend_at_deploy"]
            if val is not None:
                spend_at_deploy = val

        rate_str = f"${spend_at_deploy:.2f}/hr"
        if velocity.is_spiking and getattr(velocity, "culprit_hash", None) == dep["commit_hash"]:
            status_text.append(
                f"  {time_str}  {hash_str}  {msg:<30} {rate_str} → ${hourly_spend:.2f}/hr ← SPIKE\n",
                style="red",
            )
        else:
            status_text.append(f"  {time_str}  {hash_str}  {msg:<30} {rate_str} (normal)\n")

    if alert_sent:
        status_text.append(f"\n✦ Alert sent          {alert_sent}\n", style="bold yellow")

    if recommendation:
        status_text.append(f"✦ Recommendation      {recommendation}\n", style="bold")

    panel = Panel(
        status_text, title="SpendSentry — Spend Monitor", border_style="blue", expand=False
    )
    console.print(panel)
