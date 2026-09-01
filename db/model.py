from pydantic import BaseModel
from datetime import date


class User(BaseModel):
    id: int
    name: str
    notify: bool
    threshold: int


class NetUsage(BaseModel):
    id: int
    month: date
    mb: int
