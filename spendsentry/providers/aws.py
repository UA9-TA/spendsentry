from datetime import datetime, timedelta, timezone

import boto3

from spendsentry.providers.base import SpendData, SpendProvider


class AWSSpendProvider(SpendProvider):
    def __init__(self):
        self.client = boto3.client("ce", region_name="us-east-1")

    def get_current_spend(self) -> SpendData:
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_hour = now.replace(minute=0, second=0, microsecond=0)

        # Get daily spend (from start of day to now)
        try:
            daily_res = self.client.get_cost_and_usage(
                TimePeriod={
                    "Start": start_of_day.strftime("%Y-%m-%d"),
                    "End": (start_of_day + timedelta(days=1)).strftime("%Y-%m-%d"),
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
            )
            daily_cost = float(daily_res["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])
        except Exception:
            daily_cost = 0.0

        # Get hourly spend
        # Note: AWS Cost Explorer requires 1 day minimum interval for dates but allows HOURLY granularity
        # For current hour, we approximate or take the last available hour.

        # We need to query the last 24 hours to get HOURLY data.
        time_start = (start_of_hour - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
        time_end = start_of_hour.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            hourly_res = self.client.get_cost_and_usage(
                TimePeriod={"Start": time_start, "End": time_end},
                Granularity="HOURLY",
                Metrics=["UnblendedCost"],
            )
            # Find the most recent hour
            results = hourly_res.get("ResultsByTime", [])
            hourly_cost = 0.0
            if results:
                hourly_cost = float(results[-1]["Total"]["UnblendedCost"]["Amount"])

        except Exception:
            hourly_cost = 0.0
            hourly_res = {}

        return SpendData(
            hourly_cost=hourly_cost, daily_cost=daily_cost, timestamp=now, raw_data=hourly_res
        )

    def get_historical_spend(self, days: int = 7):
        now = datetime.now(timezone.utc)
        start_time = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        res = self.client.get_cost_and_usage(
            TimePeriod={"Start": start_time, "End": end_time},
            Granularity="HOURLY",
            Metrics=["UnblendedCost"],
        )
        return res
