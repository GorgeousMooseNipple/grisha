import logging
import httpx
from pydantic import TypeAdapter
from typing import Optional

from utils.config import CONFIG
from .model import VmInfo, BandwidthUsage

logger = logging.getLogger(__name__)


BASE_URL = "https://api.crownpanel.com"
TIMEOUT = 10


class CCApi:
    def __init__(self):
        self.client = httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(retries=3),
            timeout=TIMEOUT,
        )

    async def shutdown(self):
        await self.client.aclose()

    async def list_vms(self) -> list[VmInfo]:
        data = {
            "API_KEY": CONFIG.creds.cc_token,
            "QUERY": "list_vms",
        }

        resp = await self.client.post(BASE_URL, data=data)
        logger.debug(f"Got status {resp.status_code}, '{resp.text}'")
        resp.raise_for_status()

        return TypeAdapter(list[VmInfo]).validate_json(resp.text)

    async def vm_by_ip(self, ip: str) -> Optional[VmInfo]:
        vm_list = await self.list_vms()
        for vm in vm_list:
            if vm.ipaddress == ip:
                return vm
        return None

    async def bandwidth_usage(self, vmid: str) -> BandwidthUsage:
        data = {
            "API_KEY": CONFIG.creds.cc_token,
            "QUERY": "bandwidth_usage_v2",
            "VMID": vmid,
        }

        resp = await self.client.post(BASE_URL, data=data)
        logger.debug(f"Got status {resp.status_code}, '{resp.text}'")
        resp.raise_for_status()

        return BandwidthUsage.model_validate_json(resp.text)
