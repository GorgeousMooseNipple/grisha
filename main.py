import os
import logging
import handlers.commands
import handlers.messages
from logging.handlers import RotatingFileHandler
from telegram.ext import ApplicationBuilder, Application
from utils import CONFIG
from cc import CCApi
from db import DbApi
from jobs.notifications import update_usage


log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
log_fmt = logging.Formatter(
    "[%(asctime)s] %(module)s:%(lineno)s [%(levelname)s]: %(message)s"
)
fmt = logging.Formatter

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


async def setup(app: Application):
    logger.debug("Running global setup")

    cc_client = CCApi()
    app.bot_data["cc_client"] = cc_client

    vm = await cc_client.vm_by_ip(CONFIG.creds.vm_ip)
    if not vm:
        raise RuntimeError("Failed to get info on our baby!")
    app.bot_data["vm"] = vm

    db = DbApi()
    await db.init_db(CONFIG.settings.init_sql)
    app.bot_data["db"] = db

    assert app.job_queue, "JobQueue should be iniialized at this point"
    app.job_queue.run_repeating(
        update_usage,
        interval=CONFIG.settings.usage_polling_interval,
        first=10,
        name="usage_polling",
    )


async def teardown(app: Application):
    logger.debug("Running global teardown")
    cc_client: CCApi = app.bot_data.get("cc_client")
    if cc_client:
        await cc_client.shutdown()


if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(CONFIG.creds.telegram_token)
        .post_init(setup)
        .post_stop(teardown)
        .build()
    )

    app.add_handler(handlers.commands.start_handler)
    app.add_handler(handlers.commands.usage_handler)
    app.add_handler(handlers.commands.stats_handler)
    app.add_handler(handlers.commands.threshold_handler)
    app.add_handler(handlers.commands.notify_handler)
    app.add_handler(handlers.commands.shutup_handler)
    app.add_handler(handlers.commands.fallback_handler)

    app.add_handler(handlers.messages.image_handler)
    app.add_handler(handlers.messages.fallback_message_handler)

    logger.info("Polling for updates...")
    app.run_polling()
