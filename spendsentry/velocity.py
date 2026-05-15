from dataclasses import dataclass
from datetime import datetime


@dataclass
class VelocityReport:
    current_hourly_rate: float
    baseline_hourly_rate: float
    acceleration_factor: float
    is_spiking: bool
    spike_started_at: datetime | None


def calculate_velocity(recent_snapshots) -> VelocityReport:
    if not recent_snapshots:
        return VelocityReport(0.0, 0.0, 0.0, False, None)

    current_snapshot = recent_snapshots[0]
    current_hourly_rate = float(current_snapshot["hourly_cost"])
    current_time = datetime.fromisoformat(current_snapshot["timestamp"])

    # Calculate baseline (e.g., average of the same hour over the last 7 days)
    # For simplicity, let's just average all available previous hours if < 7 days
    if len(recent_snapshots) > 1:
        past_costs = [float(s["hourly_cost"]) for s in recent_snapshots[1:]]
        baseline_hourly_rate = sum(past_costs) / len(past_costs)
    else:
        baseline_hourly_rate = current_hourly_rate

    # Prevent division by zero
    if baseline_hourly_rate == 0:
        baseline_hourly_rate = 0.01

    acceleration_factor = current_hourly_rate / baseline_hourly_rate
    is_spiking = (
        acceleration_factor > 2.5 and current_hourly_rate > 0.1
    )  # Require at least 10 cents to spike

    spike_started_at = None
    if is_spiking:
        # Find when it started spiking
        for s in recent_snapshots:
            rate = float(s["hourly_cost"])
            if rate / baseline_hourly_rate <= 2.5:
                break
            spike_started_at = datetime.fromisoformat(s["timestamp"])

    if not spike_started_at and is_spiking:
        spike_started_at = current_time

    return VelocityReport(
        current_hourly_rate=current_hourly_rate,
        baseline_hourly_rate=baseline_hourly_rate,
        acceleration_factor=acceleration_factor,
        is_spiking=is_spiking,
        spike_started_at=spike_started_at,
    )
