import os
import logging
import handlers.commands
import handlers.messages
from logging.handlers import RotatingFileHandler
from telegram.ext import ApplicationBuilder
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

fh = RotatingFileHandler(
    filename=CONFIG.settings.log_file,
    maxBytes=50 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
fh.setLevel(log_level)
fh.setFormatter(log_fmt)

logger.addHandler(sh)
logger.addHandler(fh)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("aiosqlite").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


if __name__ == "__main__":
    app = ApplicationBuilder().token(CONFIG.creds.telegram_token).build()

    app.add_handler(handlers.commands.start_handler)
    app.add_handler(handlers.commands.fallback_handler)
    app.add_handler(handlers.messages.fallback_message_handler)

    logger.info("Polling for updates...")
    app.run_polling()
