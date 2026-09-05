from pydantic import BaseModel
from datetime import date
from utils.utils import mb_pretty


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

    def used_pretty(self) -> str:
        return mb_pretty(self.used)

    def quota_pretty(self) -> str:
        return mb_pretty(self.quota)
