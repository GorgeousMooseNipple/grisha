import logging
import random
from typing import cast
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from assets import replies
from cc import CCApi, VmInfo


logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Start update: {update}")
    user = update.effective_user
    if not user:
        logger.warning("User not set for /start command")
        return
    logger.info(f"Got /start command from: {user.username}({user.id})")
    greeting = replies.GREETINGS.format(name=user.first_name)
    await context.bot.send_message(user.id, text=greeting)


async def current_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Usage update: {update}")
    user = update.effective_user
    if not user:
        logger.warning("User not set for /usage command")
        return
    logger.info(f"Got /usage command from: {user.username}({user.id})")

    cc_client = cast(CCApi, context.bot_data.get("cc_client"))
    if not cc_client:
        logger.error(f"CC client is not initialized: {cc_client}")
        reply = random.choice(replies.BOT_ERROR)
        await context.bot.send_message(user.id, text=reply)
        return

    vm: VmInfo = context.bot_data["vm"]
    usage_result = await cc_client.bandwidth_usage(vm.id)
    if usage_result.is_err():
        logger.error(f"Getting usage: {usage_result.err}")
        reply = random.choice(replies.BOT_ERROR)
        await context.bot.send_message(user.id, text=reply)
    else:
        usage = usage_result.data
        logger.debug(f"Got usage: {usage}")
        usage_reply = replies.USAGE_REPLY.format(
            percent=round(usage.used_percentage, 2),
            used=usage.used_pretty(),
            quota=usage.quota_pretty(),
        )
        await context.bot.send_message(user.id, text=usage_reply)


async def fallback_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Fallback command update: {update}")
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    logger.info(f"Got command '{message.text}' from: {user.username}({user.id})")
    await message.reply_text(replies.UNKNOWN_COMMAND)


start_handler = CommandHandler("start", start)
usage_handler = CommandHandler("usage", current_usage)
fallback_handler = MessageHandler(filters.COMMAND, fallback_command)
