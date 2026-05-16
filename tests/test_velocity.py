from datetime import datetime, timezone

from spendsentry.velocity import calculate_velocity


def test_calculate_velocity_no_spike():
    now = datetime.now(timezone.utc)
    report = calculate_velocity(1.0, [0.9, 1.1, 1.0, 1.0], now)
    assert report.is_spiking is False
    assert round(report.baseline_hourly_rate, 2) == 1.0
    assert report.acceleration_factor == 1.0


def test_calculate_velocity_with_spike():
    now = datetime.now(timezone.utc)
    report = calculate_velocity(3.0, [1.0, 1.0, 1.0], now)
    assert report.is_spiking is True
    assert report.baseline_hourly_rate == 1.0
    assert report.acceleration_factor == 3.0
    assert report.spike_started_at == now


def test_calculate_velocity_zero_baseline():
    now = datetime.now(timezone.utc)
    report = calculate_velocity(1.0, [0.0, 0.0], now)
    assert report.is_spiking is True
    assert report.acceleration_factor == float("inf")
