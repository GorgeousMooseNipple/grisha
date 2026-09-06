import logging
from telegram.ext import ContextTypes
from db import DbApi
from db.model import YearMonth
from cc import CCApi, VmInfo
from assets import replies


logger = logging.getLogger(__name__)


async def update_usage(context: ContextTypes.DEFAULT_TYPE):
    db: DbApi = context.bot_data["db"]
    cc_client: CCApi = context.bot_data["cc_client"]
    vm: VmInfo = context.bot_data["vm"]

    usage = await cc_client.bandwidth_usage(vm.id)
    if usage.is_err():
        logger.error(f"Getting usage: {usage.err}")
        return

    usage = usage.data
    logger.info(f"Current usage: {usage}")

    year_month = YearMonth.today()
    last_usage_record = await db.last_usage()
    if not last_usage_record or usage.used < last_usage_record.used:
        logger.info(f"Creating new usage record in DB for {year_month}")
        try:
            await db.create_usage_record(usage)
            await db.reset_notified_statuses()
        except Exception as e:
            logger.error(f"Failed to create usage record for {year_month} with {e}")
    else:
        logger.info(f"Updating usage record in DB for {year_month}")
        try:
            await db.update_usage(last_usage_record.id, usage)
        except Exception as e:
            logger.error(f"Failed to update usage record with {e}")

    try:
        users = await db.should_notify(usage.used_percentage)
        logger.info(f"Should notify {len(users)} users")
    except Exception as e:
        logger.error(f"Failed to fetch users we should notify from DB with {e}")
        return

    for user in users:
        logger.debug(f"Sending usage notification to {user}")
        try:
            notification = replies.USAGE_NOTIFICATION.format(
                percent=round(usage.used_percentage, 2),
                used=usage.used_pretty(),
                quota=usage.quota_pretty(),
            )
            await context.bot.send_message(user.id, text=notification)
            await db.set_notified(user.id)
        except Exception as e:
            logger.error(f"Failed to notify {user} of current usage passing threshold")
