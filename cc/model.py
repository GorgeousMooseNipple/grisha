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

    def _mb_pretty(self, mb: float) -> str:
        units = ("Kb", "Mb", "Gb")
        value = mb * 1024.0

        for unit in units:
            pretty = f"{value:.2f} {unit}"
            if abs(value) < 1024:
                break
            value /= 1024.0
        return pretty

    def used_pretty(self) -> str:
        return self._mb_pretty(self.used)

    def quota_pretty(self) -> str:
        return self._mb_pretty(self.quota)
