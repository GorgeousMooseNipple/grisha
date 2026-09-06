from pydantic import BaseModel, field_validator, field_serializer, ConfigDict
from datetime import date
from utils.utils import mb_pretty


YEAR_MONTH_FMT = "%Y-%m"


class User(BaseModel):
    id: int
    username: str
    name: str
    notify: bool
    was_notified: bool = False
    threshold: int


class YearMonth(date):
    @staticmethod
    def from_str(year_month: str) -> "YearMonth":
        return YearMonth.strptime(year_month, YEAR_MONTH_FMT)

    def __str__(self) -> str:
        return self.strftime(YEAR_MONTH_FMT)

    def __eq__(self, other) -> bool:
        if isinstance(other, date):
            return other.year == self.year and other.month == self.month
        return super().__eq__(other)


class NetUsage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    year_month: YearMonth
    quota: float
    used: float

    @field_validator("year_month", mode="before")
    @classmethod
    def year_month_from_str(cls, year_month: str) -> YearMonth:
        return YearMonth.from_str(year_month)

    @field_serializer("year_month")
    def year_month_to_str(self, year_month: date) -> str:
        return str(year_month)

    def used_pretty(self) -> str:
        return mb_pretty(self.used)

    def quota_pretty(self) -> str:
        return mb_pretty(self.quota)
