import logging
import httpx
from pydantic import TypeAdapter
from typing import Optional

from utils.config import CONFIG
from utils.error import Result
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

    async def list_vms(self) -> Result[list[VmInfo]]:
        data = {
            "API_KEY": CONFIG.creds.cc_token,
            "QUERY": "list_vms",
        }

        resp = await self.client.post(BASE_URL, data=data)
        logger.debug(f"list_vms: Got status {resp.status_code}, '{resp.text}'")
        if not resp.is_success:
            return Result.error(
                f"Getting list of vms: got status code {resp.status_code}, '{resp.text}'"
            )

        try:
            parsed = TypeAdapter(list[VmInfo]).validate_json(resp.text)
        except Exception as e:
            return Result.error(e)
        return Result.ok(parsed)

    async def vm_by_ip(self, ip: str) -> Optional[VmInfo]:
        vm_list = await self.list_vms()
        if vm_list.is_err():
            logger.error(f"Failed to get lis of vms with: {vm_list.err}")
            return None

        for vm in vm_list.data:
            if vm.ipaddress == ip:
                return vm
        return None

    async def bandwidth_usage(self, vmid: str) -> Result[BandwidthUsage]:
        data = {
            "API_KEY": CONFIG.creds.cc_token,
            "QUERY": "bandwidth_usage_v2",
            "VMID": vmid,
        }

        resp = await self.client.post(BASE_URL, data=data)
        logger.debug(
            f"bandwidth_usage_v2: Got status {resp.status_code}, '{resp.text}'"
        )
        if not resp.is_success:
            return Result.error(
                f"Getting bandwidth usage: got status code {resp.status_code}, '{resp.text}'"
            )

        try:
            usage = BandwidthUsage.model_validate_json(resp.text)
        except Exception as e:
            return Result.error(e)
        return Result.ok(usage)
