import os
import logging
import asyncio


log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
log_fmt = logging.Formatter("%(module)s:%(lineno)s [%(levelname)s]: %(message)s")

logger = logging.getLogger()
logger.setLevel(log_level)
sh = logging.StreamHandler()
sh.setLevel(log_level)
sh.setFormatter(log_fmt)
logger.addHandler(sh)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("aiosqlite").setLevel(logging.WARNING)


from utils import CONFIG
from cc import CCApi
from db import DbApi


async def main():
    cc_api = CCApi()
    vm = await cc_api.vm_by_ip(CONFIG.creds.vm_ip)
    assert vm is not None
    logger.info(f"Our baby: {vm}")
    usage = await cc_api.bandwidth_usage(vm.id)
    if usage.is_ok():
        logger.info(f"Usage: {usage.data}")
    else:
        logger.error(f"Error getting usage: {usage.err}")
    await cc_api.shutdown()
    db = DbApi()
    await db.init_db(CONFIG.settings.init_sql)
    users = await db.users_with_notification()
    for user in users:
        logger.info(f"Got user: {user}")


if __name__ == "__main__":
    asyncio.run(main())
