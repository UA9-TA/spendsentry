from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_status(
    spend_today: float,
    limit_today: float,
    current_hourly: float,
    is_spiking: bool,
    spike_started_at: datetime,
    commits: list,
    alert_sent: str,
    recommendation: str,
):

    status_text = Text()

    # Today's spend
    limit_str = f"(limit: ${limit_today:.2f})" if limit_today else ""
    status_text.append(f"✦ Today's spend       ${spend_today:.2f}  {limit_str}\n")

    # Last hour
    spike_text = "⚠ HIGH — 3× normal rate" if is_spiking else "Normal"
    status_text.append(f"✦ Last hour           ${current_hourly:.2f}  {spike_text}\n")

    # Spend velocity
    if is_spiking and spike_started_at:
        status_text.append(
            f"✦ Spend velocity      ↑ accelerating since {spike_started_at.strftime('%H:%M')}\n"
        )
    else:
        status_text.append("✦ Spend velocity      steady\n")

    status_text.append("\n  Recent deployments:\n")

    for i, commit in enumerate(commits):
        time_str = commit["timestamp"].strftime("%H:%M")
        hash_str = commit["hash"][:7]
        msg = commit["message"][:30].ljust(30)

        if is_spiking and i == 0:
            status_text.append(
                f"  {time_str}  {hash_str}  {msg}  ${commit.get('spend_at_deploy', 0):.2f} → ${current_hourly:.2f}/hr ← SPIKE\n"
            )
        else:
            status_text.append(
                f"  {time_str}  {hash_str}  {msg}  ${commit.get('spend_at_deploy', 0):.2f}/hr (normal)\n"
            )

    if alert_sent:
        status_text.append(f"\n✦ Alert sent          {alert_sent}\n")
    if recommendation:
        status_text.append(f"✦ Recommendation      {recommendation}\n")

    panel = Panel(status_text, title="SpendSentry — Spend Monitor", expand=False)
    console.print(panel)
