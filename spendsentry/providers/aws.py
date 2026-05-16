from datetime import datetime, timedelta, timezone

import boto3

from spendsentry.providers.base import SpendProvider


class AWSProvider(SpendProvider):
    def __init__(self):
        self.client = boto3.client("ce")

    def _get_time_period(self, start_dt: datetime, end_dt: datetime):
        return {
            "Start": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "End": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    def get_current_hourly_spend(self) -> float:
        # Get spend for the current hour
        now = datetime.now(timezone.utc)
        start = now.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)

        response = self.client.get_cost_and_usage(
            TimePeriod=self._get_time_period(start, end),
            Granularity="HOURLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        total = 0.0
        for result in response.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                amount = group["Metrics"]["UnblendedCost"]["Amount"]
                total += float(amount)

        return total

    def get_todays_spend(self) -> float:
        # Get spend for today
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        response = self.client.get_cost_and_usage(
            TimePeriod=self._get_time_period(start, end),
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
        )

        total = 0.0
        for result in response.get("ResultsByTime", []):
            total += float(result["Total"]["UnblendedCost"]["Amount"])

        return total

    def get_spend_history(self, days: int) -> list[dict]:
        now = datetime.now(timezone.utc)
        end = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        start = end - timedelta(days=days)

        response = self.client.get_cost_and_usage(
            TimePeriod=self._get_time_period(start, end),
            Granularity="HOURLY",
            Metrics=["UnblendedCost"],
        )

        history = []
        for result in response.get("ResultsByTime", []):
            timestamp_str = result["TimePeriod"]["Start"]
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            amount = float(result["Total"]["UnblendedCost"]["Amount"])
            history.append({"timestamp": timestamp, "hourly_cost": amount})

        return history
