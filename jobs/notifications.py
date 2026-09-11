import httpx
import logging
import telegram.error
from telegram.ext import ContextTypes
from db import DbApi
from db.model import YearMonth
from cc import CCApi, VmInfo
from assets import replies
from utils.config import CONFIG
from utils.utils import url_base


logger = logging.getLogger(__name__)


async def update_usage(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Polling current usage")
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
        logger.debug(f"Current latest usage record: {last_usage_record}")
        try:
            await db.update_usage(last_usage_record.id, usage)
        except Exception as e:
            logger.error(f"Failed to update usage record with {e}")

    try:
        users = await db.should_notify_usage(usage.used_percentage)
    except Exception as e:
        logger.error(f"Failed to fetch users we should notify from DB with {e}")
        return

    logger.info(f"Sending usage notification to {len(users)} users")
    for user in users:
        try:
            notification = replies.USAGE_NOTIFICATION.format(
                percent=round(usage.used_percentage, 2),
                used=usage.used_pretty(),
                quota=usage.quota_pretty(),
            )
            await context.bot.send_message(user.id, text=notification)
            await db.set_notified(user.id)
            logger.debug(f"Sent usage notification for {user}")
        except telegram.error.Forbidden as e:
            logger.warning(f"User {user} seems to block/delete chat: {e}")
            await db.disable_notifications(user.id)
        except Exception as e:
            logger.error(f"Failed to notify {user} of current usage passing threshold")


async def _get_exchange_rate(rates_url: str) -> float:
    async with httpx.AsyncClient() as client:
        resp = await client.get(rates_url, timeout=15)
        resp.raise_for_status()
        j_rates = resp.json()
        rate = j_rates[0]
        return rate["rate"]


async def notify_monthly(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending monthly notification")
    db: DbApi = context.bot_data["db"]
    try:
        users = await db.users_with_notification()
    except Exception as e:
        logger.error(
            f"Failed to get users with notificaions for monthly update with {e}"
        )
        raise

    logger.info(f"Should notify {len(users)} users")
    if not users:
        return
    rate_info = ""
    #  rates_url = CONFIG.settings.rates_url
    #  try:
    #      if rates_url:
    #          current_rate = await _get_exchange_rate(rates_url)
    #          rate_info = f"Согласно '{url_base(rates_url)}', текущий курс: {current_rate} рубля (может быть просрочен на сутки)"
    #  except Exception as e:
    #      logger.error(f"Failed to get current rate from '{rates_url}' with {e}")

    reply = replies.MONTHLY_NOTIFICATION.format(exchange_rate_info=rate_info)
    for user in users:
        logger.debug(f"Monthly notification for {user}")
        try:
            await context.bot.send_message(user.id, text=reply)
        except telegram.error.Forbidden as e:
            logger.warning(f"User {user} seems to block/delete chat: {e}")
            await db.disable_notifications(user.id)
