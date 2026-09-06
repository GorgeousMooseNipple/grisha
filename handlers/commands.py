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
    if await db.user_by_id(user.id):
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

    if limit is not None and limit < 1:
        logger.error(f"Stats given invalid limit {limit}")
        await context.bot.send_message(
            user.id, text=f"Это должно быть положительное целое число, а не {limit}))"
        )
        return

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


async def set_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Threshold update: {update}")
    user = update.effective_user
    if not user:
        logger.warning("User not set for /threshold command")
        return

    args = context.args
    logger.info(
        f"Got /threshold command from: {user.username}({user.id}) with args: {args}"
    )
    if not args:
        logger.warning("/threshold called with no arguments")
        await context.bot.send_message(
            user.id, text="С этой командой нужно передать число от 1 до 99!"
        )
        return

    first, *rest = args
    try:
        new_threshold = int(first)
    except ValueError:
        logger.warning(f"/threshold expects integer, got {first}")
        await context.bot.send_message(
            user.id, text=f"'{first}'?? Was?) И тебе {first})"
        )
        return

    if new_threshold < 1 or new_threshold > 99:
        logger.warning(f"Invalid threshold {new_threshold} given")
        await context.bot.send_message(user.id, text=f"Число от 1 до 99, bitte)")
        return

    db: DbApi = context.bot_data["db"]
    existing_user = await db.user_by_id(user.id)
    if not existing_user:
        logger.error(f"/threshold request from unrecognized {user}")
        await context.bot.send_message(user.id, text=f"Подожди, а ты как сюда попал?!")
        return

    if new_threshold == existing_user.threshold:
        logger.info(f"/threshold request from unrecognized {user}")
        await context.bot.send_message(
            user.id, text=f"Schönheit! Мне даже делать ничего не пришлось)"
        )
        return

    try:
        await db.set_threshold(existing_user.id, new_threshold)
        reply = "Готово!\n"
        if rest:
            reply += f"P.S. а вот как с этим быть я не понял: '{' '.join(rest)}'"
    except Exception as e:
        logger.error(
            f"Failed to set threshold to {new_threshold} for {existing_user} with {e}"
        )
        reply = random.choice(replies.BOT_ERROR)
    await context.bot.send_message(user.id, text=reply)


async def enable_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Notify update: {update}")
    user = update.effective_user
    if not user:
        logger.warning("User not set for /notify command")
        return
    logger.info(f"Got /notify command from: {user.username}({user.id})")

    db: DbApi = context.bot_data["db"]
    existing_user = await db.user_by_id(user.id)
    if not existing_user:
        logger.error(f"{user} is not registered in DB")
        await context.bot.send_message(
            user.id, text="Подожди секунду, а я тебя точно знаю?"
        )
        return

    if existing_user.notify:
        logger.info(f"{existing_user} already enabled notifications")
        await context.bot.send_message(
            user.id, text="Уведомления уже включены! Ihre Gesundheit!"
        )
        return

    try:
        await db.enable_notifications(existing_user.id)
        await context.bot.send_message(
            user.id, text="Договорились, буду держать тебя в курсе)"
        )
    except Exception as e:
        logger.error(f"Failed to enable notifications for {existing_user} with {e}")
        reply = random.choice(replies.BOT_ERROR)
        await context.bot.send_message(user.id, text=reply)


async def shut_up_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/shutup update: {update}")
    user = update.effective_user
    if not user:
        logger.warning("User not set for /shutup command")
        return
    logger.info(f"Got /shutup command from: {user.username}({user.id})")

    db: DbApi = context.bot_data["db"]
    existing_user = await db.user_by_id(user.id)
    if not existing_user:
        logger.error(f"{user} is not registered in DB")
        await context.bot.send_message(
            user.id, text="Подожди секунду, а я тебя точно знаю?"
        )
        return

    if not existing_user.notify:
        logger.info(f"{existing_user} already disabled notifications")
        await context.bot.send_message(user.id, text="Все, я уже заткнулся)")
        return

    try:
        await db.disable_notifications(existing_user.id)
        await context.bot.send_message(
            user.id,
            text="Без проблем, набери меня, если передумаешь) Oh Ich denke nur an Bier!",
        )
    except Exception as e:
        logger.error(f"Failed to disable notifications for {existing_user} with {e}")
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
threshold_handler = CommandHandler("threshold", set_threshold)
notify_handler = CommandHandler("notify", enable_notifications)
shutup_handler = CommandHandler("shutup", shut_up_notifications)
fallback_handler = MessageHandler(filters.COMMAND, fallback_command)
