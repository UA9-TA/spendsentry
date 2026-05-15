from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SpendData:
    hourly_cost: float
    daily_cost: float
    timestamp: datetime
    raw_data: dict = None


class SpendProvider(ABC):
    @abstractmethod
    def get_current_spend(self) -> SpendData:
        pass

    @abstractmethod
    def get_historical_spend(self, days: int):
        pass
