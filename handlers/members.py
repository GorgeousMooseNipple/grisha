import logging
from telegram import Update, ChatMember
from telegram.ext import (
    ContextTypes,
    ChatMemberHandler,
)
from db import DbApi


logger = logging.getLogger(__name__)


async def handle_chat_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Handling status change for {update.effective_user}")
    query = update.my_chat_member
    if not query:
        logger.error("Chat status change is not set")
        return

    old_status = query.old_chat_member.status
    new_status = query.new_chat_member.status
    user_id = query.from_user.id
    username = query.from_user.username
    user_str = f"{username}({user_id})"

    logger.info(f"Status change: {user_id=}, {username=}, {old_status=}, {new_status=}")

    if query.chat.type != "private":
        logger.warning("Status change not in private chat")
        return

    if new_status in (ChatMember.LEFT, ChatMember.BANNED):
        logger.debug(f"{user_str} deleted chat/blocked bot - disabling notifications")
        db: DbApi = context.bot_data["db"]
        existing_user = await db.user_by_id(user_id)
        if not existing_user:
            logger.warning(f"{user_str} was not registered in DB")
            return

        logger.info(f"Disabling notifications for {user_str}")
        await db.disable_notifications(existing_user.id)
    elif new_status == ChatMember.MEMBER:
        logger.debug(f"{user_str} came back/unblocked bot")
        return


status_handler = ChatMemberHandler(handle_chat_status, ChatMemberHandler.MY_CHAT_MEMBER)
