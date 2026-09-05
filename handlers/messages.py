import logging
import random
from pathlib import Path
from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)
from assets import replies
from utils import CONFIG


logger = logging.getLogger(__name__)


async def confused_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Fallback message update: {update}")
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    logger.info(f"Got message '{message.text}' from: {user.username}({user.id})")
    if message.text and "пив" in message.text.casefold():
        reply = random.choice(replies.BEER_REPLIES)
    else:
        reply = random.choice(replies.CONFUSED_REPLIES)
    await context.bot.send_message(user.id, text=reply)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Image message update: {update}")
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    logger.info(f"Got message with image from: {user.username}({user.id})")
    storage = Path(CONFIG.settings.storage_path)
    if not storage.exists():
        await context.bot.send_message(
            user.id, text="Спасибо, но мне и повесить некуда! Надо порядок навести"
        )
        return

    image_path = storage.joinpath(
        f"{user.username or user.first_name}_{message.id}.jpg"
    )
    try:
        image_file = await message.photo[-1].get_file()
        await image_file.download_to_drive(image_path)
        logger.debug(f"Saved image at '{image_path}'")
        await context.bot.send_message(user.id, text=replies.IMAGE_REPLY)
    except Exception as e:
        logger.error(f"Saving image: {e}")
        reply = random.choice(replies.BOT_ERROR)
        await context.bot.send_message(user.id, text=reply)


image_handler = MessageHandler(filters.PHOTO, handle_image)
fallback_message_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND, confused_reply
)
