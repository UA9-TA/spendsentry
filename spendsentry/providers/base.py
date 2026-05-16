from abc import ABC, abstractmethod


class SpendProvider(ABC):
    @abstractmethod
    def get_current_hourly_spend(self) -> float:
        """Returns the spend for the current hour."""
        pass

    @abstractmethod
    def get_todays_spend(self) -> float:
        """Returns the spend for today."""
        pass

    @abstractmethod
    def get_spend_history(self, days: int) -> list[dict]:
        """Returns historical spend data."""
        pass
