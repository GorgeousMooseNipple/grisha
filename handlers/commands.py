import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from assets import replies


logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Start update: {update}")
    user = update.effective_user
    if not user:
        return
    logger.info(f"Got /start command from: {user.username}({user.id})")
    greeting = replies.GREETINGS.format(name=user.first_name)
    await context.bot.send_message(user.id, text=greeting)


async def fallback_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Fallback command update: {update}")
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    logger.info(f"Got command '{message.text}' from: {user.username}({user.id})")
    await message.reply_text(replies.UNKNOWN_COMMAND)


start_handler = CommandHandler("start", start)
fallback_handler = MessageHandler(filters.COMMAND, fallback_command)
