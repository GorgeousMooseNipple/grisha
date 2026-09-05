from pydantic import BaseModel, Field
from utils.utils import mb_pretty


class VmInfo(BaseModel):
    id: str = Field(alias="vmid")
    status: str
    hostname: str
    ipaddress: str
    location: str
    bandwidth: int


class BandwidthUsage(BaseModel):
    used: float = Field(alias="bandwidth_usage")
    quota: float = Field(alias="bandwidth_quota")
    used_percentage: float = Field(alias="bandwidth_usage_percentage")

    def used_pretty(self) -> str:
        return mb_pretty(self.used)

    def quota_pretty(self) -> str:
        return mb_pretty(self.quota)
