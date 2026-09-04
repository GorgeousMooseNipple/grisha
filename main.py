import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from utils import CONFIG
from cc import CCApi
from db import DbApi


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
logging.getLogger("telegram").setLevel(logging.WARNING)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    logger.debug(f"Got /start command from: {user.username}({user.id})")
    await context.bot.send_message(user.id, text="Hello there!")


async def repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    logger.debug(f"Got message '{message.text}' from: {user.username}({user.id})")
    await context.bot.send_message(user.id, text=f"You said: {message.text}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(CONFIG.creds.telegram_token).build()
    start_handler = CommandHandler("start", start)
    repeat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, repeat)

    app.add_handler(start_handler)
    app.add_handler(repeat_handler)

    logger.info("Polling for updates...")
    app.run_polling()
