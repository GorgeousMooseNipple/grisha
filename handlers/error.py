import json
import html
import logging
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.config import CONFIG


logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(
        None,
        value=context.error,
        tb=context.error.__traceback__,  # type: ignore
    )
    tb_str = "".join(tb_list[:30])

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=4, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_str)}</pre>"
    )

    await context.bot.send_message(
        chat_id=CONFIG.creds.dev_id, text=message, parse_mode=ParseMode.HTML
    )
