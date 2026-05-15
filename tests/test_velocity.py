import json
from datetime import datetime
from pathlib import Path

from spendsentry.velocity import calculate_velocity

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_velocity_detection():
    with open(FIXTURES_DIR / "sample_spend_history.json") as f:
        snapshots = json.load(f)

    velocity = calculate_velocity(snapshots)

    # Assertions based on the mocked logic
    # Baseline will be avg of (1.50, 0.20, 0.18, 0.19, 0.21, 0.18) = 2.46 / 6 = 0.41
    # Current is 1.83
    # Factor = 1.83 / 0.41 = 4.46 > 2.5 (Spiking!)

    assert velocity.current_hourly_rate == 1.83
    assert velocity.is_spiking is True
    assert velocity.acceleration_factor > 2.5

    # Should detect spike started when it jumped over 2.5x baseline
    # 1.50 / 0.41 = 3.65 (also spiking)
    # 0.20 / 0.41 = 0.48 (not spiking)
    # Spike started at 09:00
    assert velocity.spike_started_at is not None
    assert velocity.spike_started_at == datetime.fromisoformat("2023-10-25T09:00:00+00:00")
