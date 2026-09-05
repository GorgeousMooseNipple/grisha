import logging
import random
from typing import cast, Optional
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from assets import replies
from cc import CCApi, VmInfo
from db import DbApi
from db.model import YearMonth, User
from utils.config import CONFIG


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

    db: DbApi = context.bot_data["db"]
    if await db.user_exists(user.id):
        logger.info(f"{user} already saved to DB")
        await context.bot.send_message(
            user.id, text="Рад снова встретить! Willkommen zurück!"
        )
        return
    try:
        user = User(
            id=user.id,
            username=user.username or user.full_name,
            name=user.full_name,
            notify=False,
            threshold=CONFIG.settings.default_threshold,
        )
        await db.insert_user(user)
        logger.debug(f"Success creating user {user}")
    except Exception as e:
        logger.error(f"Failed to create user with {e}. User in question: {user}")
        await context.bot.send_message(
            user.id, text="Freund, что-то пошло не так с добавлением тебя в бд!!!"
        )


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


def _parse_stats_arg(arg: str) -> tuple[Optional[int], Optional[YearMonth]]:
    try:
        return int(arg), None
    except ValueError:
        pass

    return None, YearMonth.from_str(arg)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Stats update: {update}")
    user = update.effective_user
    if not user:
        logger.warning("User not set for /stats command")
        return

    args = context.args
    logger.info(
        f"Got /stats command from: {user.username}({user.id}) with args: {args}"
    )

    limit = 6
    since = None
    unhandled = []
    if args:
        first, *unhandled = args
        try:
            limit, since = _parse_stats_arg(first)
        except Exception as e:
            logger.error(f"Failed to parse stats args: {args} with {e}")
            await context.bot.send_message(
                user.id,
                text=f"Freund, я не разобрал эту часть: {args}. Zu kompliziert!",
            )

    db = cast(DbApi, context.bot_data.get("db"))
    try:
        if since:
            reply = f"Статы с {since}:\n"
            stats = await db.stats_since(since)
        else:
            reply = f"Статы за последние {limit} месяцев:\n"
            stats = await db.stats(limit)

        stats_list = [
            f"{stat.year_month}: {stat.used_pretty()} из {stat.quota_pretty()}\n"
            for stat in stats
        ]

        if not stats_list:
            reply = "Oh nein! Кажется я ничего не нашел "
            reply += f"с {since} :C" if since else f"за последние {limit} месяцев :C\n"
        else:
            reply += "".join(stats_list)

        if unhandled:
            reply += (
                f"P.S. Entschuldigung, я не понял к чему было вот это: '{unhandled}'"
            )
        await context.bot.send_message(user.id, text=reply)
    except Exception as e:
        logger.error(f"Failed to get usage stats from DB with {e}")
        reply = random.choice(replies.BOT_ERROR)
        await context.bot.send_message(user.id, text=reply)


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
stats_handler = CommandHandler("stats", stats)
fallback_handler = MessageHandler(filters.COMMAND, fallback_command)
