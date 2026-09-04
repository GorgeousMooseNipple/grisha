from pydantic import BaseModel
from datetime import date


class User(BaseModel):
    id: int
    username: str
    name: str
    notify: bool
    threshold: int


class NetUsage(BaseModel):
    id: int
    month: date
    quota: int
    used: int
