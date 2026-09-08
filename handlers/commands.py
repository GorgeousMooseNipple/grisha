import logging
import random
from typing import cast, Optional
from enum import Enum
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from telegram.constants import ParseMode
from assets import replies
from cc import CCApi, VmInfo
from db import DbApi
from db.model import YearMonth, User
from utils.config import CONFIG


logger = logging.getLogger(__name__)


class CommandState(Enum):
    WAITING_INPUT = 1


async def cancel(update: Update, _: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Got /cancel command {update}")
    message = update.effective_message
    if not message:
        logger.warning("message not available for /cancel command")
        return

    await message.reply_text("Окей, поговорим о чем-нибудь другом) ...пиво?")
    return ConversationHandler.END


async def end_conversation(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return ConversationHandler.END
    logger.debug(f"{user.username}({user.id}) went off the script with '{message}'")

    await message.reply_text("Окей)")
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/start update: {update}")
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
        logger.info(f"Success creating user {user}")
    except Exception as e:
        logger.error(f"Failed to create user with {e}. User in question: {user}")
        await context.bot.send_message(
            user.id, text="Freund, что-то пошло не так с добавлением тебя в бд!!!"
        )


async def current_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/usage update: {update}")
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


async def stats_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/stats update: {update}")
    user = update.effective_user
    if not user:
        logger.warning("User not set for /stats command")
        return ConversationHandler.END

    logger.info(f"Got /stats command from: {user.username}({user.id})")
    await context.bot.send_message(
        user.id,
        text="Хорошо, за сколько прошлых месяцев стату? Дай мне число или напиши начиная с какого месяца, например '2025-08'",
    )
    return CommandState.WAITING_INPUT


async def process_stats_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        logger.warning("User or message is not set for /stats input")
        return ConversationHandler.END

    limit = 6
    since = None
    unhandled = []

    if message.text:
        first, *unhandled = message.text.split()
        try:
            limit, since = _parse_stats_arg(first)
        except Exception as e:
            logger.error(f"Failed to parse stats args: '{message.text}' with {e}")
            await message.reply_text(text=f"Freund, я не понял :( Zu kompliziert!")
            return ConversationHandler.END

    if limit is not None and limit < 1:
        logger.error(f"Stats given invalid limit {limit}")
        await message.reply_text(
            text=f"Это должно быть положительное целое число, а не {limit}))"
        )
        return ConversationHandler.END

    db = cast(DbApi, context.bot_data.get("db"))
    try:
        if since:
            reply = f"Статы с {since}:\n"
            stats = await db.stats_since(since)
        else:
            reply = f"Статы за последние {limit} месяцев:\n"
            stats = await db.stats(limit)

        pad = CONFIG.settings.stats_padding
        stats_list = [
            f"{stat.year_month}: {stat.used_pretty():<{pad}} из {stat.quota_pretty():<{pad}}\n"
            for stat in stats
        ]

        if not stats_list:
            reply = "Oh nein! Кажется я ничего не нашел "
            reply += f"с {since} :C" if since else f"за последние {limit} месяцев :C\n"
        else:
            reply += f"<pre>{''.join(stats_list)}</pre>"

        if unhandled:
            reply += (
                f"P.S. Entschuldigung, я не понял к чему было вот это: '{unhandled}'"
            )
        await message.reply_text(reply, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to get usage stats from DB with {e}")
        reply = random.choice(replies.BOT_ERROR)
        await message.reply_text(reply)

    return ConversationHandler.END


async def threshold_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/threshold update: {update}")
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        logger.warning("User or message is not set for /threshold command")
        return ConversationHandler.END
    logger.info(f"Got /threshold command from: {user.username}({user.id})")

    db: DbApi = context.bot_data["db"]
    existing_user = await db.user_by_id(user.id)
    if not existing_user:
        logger.error(f"/threshold unrecognized user: {user}")
        reply = random.choice(replies.UNKNOWN_USER)
        await message.reply_text(reply)
        return ConversationHandler.END
    logger.debug(f"/threshold for: {existing_user}")

    reply = replies.THRESHOLD_PROMPT.format(current=existing_user.threshold)
    await message.reply_text(reply)

    return CommandState.WAITING_INPUT


async def process_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Processing threshold input {update}")
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        logger.warning("User or message is not set for threshold input")
        return ConversationHandler.END

    if not message.text:
        await message.reply_text("...")
        return ConversationHandler.END

    logger.info(
        f"Processing threshold input: {user.username}({user.id}) sent '{message.text}'"
    )

    first, *rest = message.text.split()
    try:
        first = first.rstrip("%")
        new_threshold = int(first)
    except ValueError:
        logger.warning(f"/threshold expects integer, got {first}")
        await message.reply_text(text=f"'{first}'?? Was?) И тебе {first})")
        return ConversationHandler.END

    if new_threshold < 1 or new_threshold > 99:
        logger.warning(f"Invalid threshold {new_threshold} given")
        await message.reply_text(text=f"Число от 1 до 99, bitte)")
        return ConversationHandler.END

    db: DbApi = context.bot_data["db"]
    existing_user = await db.user_by_id(user.id)
    if not existing_user:
        logger.error(f"/threshold prompt from unrecognized user: {user}")
        reply = random.choice(replies.UNKNOWN_USER)
        await message.reply_text(reply)
        return ConversationHandler.END

    if new_threshold == existing_user.threshold:
        logger.info(f"Threshold unchanged for {user}")
        await message.reply_text(text=f"Schönheit! Мне даже делать ничего не пришлось)")
        return ConversationHandler.END

    try:
        await db.set_threshold(existing_user.id, new_threshold)
        reply = f"Договорились! Пришлю тебе уведомление, если использование трафика будет выше {new_threshold}%!\n"
        if rest:
            reply += f"P.S. а вот как с этим быть я не понял: '{' '.join(rest)}'"
    except Exception as e:
        logger.error(
            f"Failed to set threshold to {new_threshold} for {existing_user} with {e}"
        )
        reply = random.choice(replies.BOT_ERROR)

    await message.reply_text(text=reply)
    return ConversationHandler.END


async def enable_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"/notify update: {update}")
    user = update.effective_user
    if not user:
        logger.warning("User not set for /notify command")
        return
    logger.info(f"Got /notify command from: {user.username}({user.id})")

    db: DbApi = context.bot_data["db"]
    existing_user = await db.user_by_id(user.id)
    if not existing_user:
        logger.error(f"/notify from unrecognized user: {user}")
        reply = random.choice(replies.UNKNOWN_USER)
        await context.bot.send_message(user.id, text=reply)
        return
    logger.debug(f"Enabling notifications for {existing_user}")

    if existing_user.notify:
        logger.info(f"{existing_user} has already enabled notifications")
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
        logger.error(f"/shutup from unrecognized user: {user}")
        reply = random.choice(replies.UNKNOWN_USER)
        await context.bot.send_message(user.id, text=reply)
        return
    logger.debug(f"Disabling notifications for {existing_user}")

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
stats_handler = ConversationHandler(
    entry_points=[CommandHandler("stats", stats_init)],
    states={
        CommandState.WAITING_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_stats_input)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        MessageHandler(filters.TEXT | filters.COMMAND, end_conversation),
    ],
    conversation_timeout=60,
)
threshold_handler = ConversationHandler(
    entry_points=[CommandHandler("threshold", threshold_update)],
    states={
        CommandState.WAITING_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_threshold_input)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        MessageHandler(filters.TEXT | filters.COMMAND, end_conversation),
    ],
    conversation_timeout=60,
)
notify_handler = CommandHandler("notify", enable_notifications)
shutup_handler = CommandHandler("shutup", shut_up_notifications)
fallback_handler = MessageHandler(filters.COMMAND, fallback_command)
