from pydantic import BaseModel, Field


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
