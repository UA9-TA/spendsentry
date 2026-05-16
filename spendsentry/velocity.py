from dataclasses import dataclass
from datetime import datetime


@dataclass
class VelocityReport:
    current_hourly_rate: float
    baseline_hourly_rate: float  # 7-day average same time of day
    acceleration_factor: float  # current / baseline
    is_spiking: bool  # acceleration_factor > 2.5
    spike_started_at: datetime


def calculate_velocity(
    current_rate: float, historical_rates: list[float], current_time: datetime
) -> VelocityReport:
    # If not enough history, use a simple average or just assume no spike
    if not historical_rates:
        return VelocityReport(current_rate, current_rate, 1.0, False, current_time)

    baseline = sum(historical_rates) / len(historical_rates)

    if baseline == 0:
        if current_rate > 0:
            accel = float("inf")
        else:
            accel = 1.0
    else:
        accel = current_rate / baseline

    is_spiking = accel > 2.5

    return VelocityReport(
        current_hourly_rate=current_rate,
        baseline_hourly_rate=baseline,
        acceleration_factor=accel,
        is_spiking=is_spiking,
        spike_started_at=current_time if is_spiking else None,
    )
