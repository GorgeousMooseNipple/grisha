from pydantic import BaseModel, field_validator, field_serializer
from datetime import date
from utils.utils import mb_pretty


YEAR_MONTH_FMT = "%Y-%m"


class User(BaseModel):
    id: int
    username: str
    name: str
    notify: bool
    threshold: int


class NetUsage(BaseModel):
    id: int
    year_month: date
    quota: float
    used: float

    @field_validator("year_month", mode="before")
    @classmethod
    def year_month_from_str(cls, year_month: str) -> date:
        return date.strptime(year_month, YEAR_MONTH_FMT)

    @field_serializer("year_month")
    def year_month_to_str(self, year_month: date) -> str:
        return year_month.strftime(YEAR_MONTH_FMT)

    def used_pretty(self) -> str:
        return mb_pretty(self.used)

    def quota_pretty(self) -> str:
        return mb_pretty(self.quota)
