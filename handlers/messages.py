import logging
import random
from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)
from assets import replies


logger = logging.getLogger(__name__)


async def confused_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Fallback message update: {update}")
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    logger.info(f"Got message '{message.text}' from: {user.username}({user.id})")
    reply = random.choice(replies.CONFUSED_REPLIES)
    await context.bot.send_message(user.id, text=reply)


fallback_message_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND, confused_reply
)
