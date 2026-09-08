import logging
import aiosqlite
import math
from utils.config import CONFIG
from pathlib import Path
from typing import Optional, Iterable
from datetime import date

from .model import User, NetUsage, YearMonth
from cc.model import BandwidthUsage


logger = logging.getLogger(__name__)

USERS_TABLE = "users"
USAGE_TABLE = "net_usage"


class DbApi:
    def __init__(self):
        self.db_path = Path(CONFIG.settings.db_path)
        if not self.db_path.parent.exists():
            logger.info(f"Creating DB parent path at '{self.db_path.parent}'")
            self.db_path.parent.mkdir(parents=True)
        aiosqlite.Connection

    async def init_db(self, script_path: str | Path):
        logger.info("Initiating DB")
        script_path = Path(script_path)

        if not script_path.exists():
            raise RuntimeError(
                f"Path to DB init script does not exist at '{script_path}'"
            )

        async with aiosqlite.connect(self.db_path) as conn:
            init_script = script_path.read_text("utf-8")
            logger.info(f"Using '{init_script}' to initialize DB")
            await conn.executescript(init_script)

    @property
    async def _connection(self) -> aiosqlite.Connection:
        connection = aiosqlite.connect(self.db_path)
        connection.row_factory = aiosqlite.Row
        await connection.set_trace_callback(logger.debug)
        return connection

    async def _query_users(
        self, where: str = "", params: Optional[Iterable] = None
    ) -> list[User]:
        query = f"SELECT * FROM {USERS_TABLE}"
        if where:
            query = f"{query} {where}"
        async with await self._connection as conn:
            cursor = await conn.execute(query, params)
            user_rows = await cursor.fetchall()
            users = [User(**row) for row in user_rows]
            logger.debug(f"Got {len(users)} User records from DB")
            return users

    async def users(self) -> list[User]:
        logger.debug("Getting all users")
        return await self._query_users()

    async def users_with_notification(self) -> list[User]:
        logger.debug("Getting users with notifications enabled")
        return await self._query_users("WHERE notify = TRUE")

    async def user_by_id(self, id: int) -> Optional[User]:
        logger.debug(f"Getting user with id = {id}")
        async with await self._connection as conn:
            query = f"SELECT * FROM {USERS_TABLE} WHERE id = ?"
            cursor = await conn.execute(query, (id,))
            user = await cursor.fetchone()
            return User(**user) if user else None

    async def insert_user(self, user: User):
        logger.debug(f"Creating user {user}")
        async with await self._connection as conn:
            async with conn:
                await conn.execute(
                    f"INSERT INTO {USERS_TABLE}(id, username, name, notify, was_notified, threshold) VALUES(?, ?, ?, ?, ?, ?)",
                    (
                        user.id,
                        user.username,
                        user.name,
                        user.notify,
                        False,
                        user.threshold,
                    ),
                )

    async def set_threshold(self, user_id: int, threshold: int):
        logger.debug(f"Setting threshold to {threshold}% for user with id = {user_id}")
        async with await self._connection as conn:
            async with conn:
                query = f"UPDATE {USERS_TABLE} SET threshold = ?, was_notified = FALSE WHERE id = ?"
                await conn.execute(query, (threshold, user_id))

    async def _set_notifications(self, user_id: int, enable: bool):
        async with await self._connection as conn:
            async with conn:
                query = f"UPDATE {USERS_TABLE} SET notify = ?, was_notified = FALSE WHERE id = ?"
                await conn.execute(query, (enable, user_id))

    async def enable_notifications(self, user_id: int):
        logger.debug(f"Enabling notifications for user with id = {user_id}")
        await self._set_notifications(user_id, enable=True)

    async def disable_notifications(self, user_id: int):
        logger.debug(f"Disabling notifications for user with id = {user_id}")
        await self._set_notifications(user_id, enable=False)

    async def set_notified(self, user_id: int):
        logger.debug(f"Mark user with id = {user_id} as already notified")
        async with await self._connection as conn:
            async with conn:
                query = f"UPDATE {USERS_TABLE} SET was_notified = TRUE WHERE id = ?"
                await conn.execute(query, (user_id,))

    async def reset_notified_statuses(self):
        logger.debug(f"Resetting 'was_notified' for all users")
        query = f"UPDATE {USERS_TABLE} SET was_notified = FALSE"
        async with await self._connection as conn:
            async with conn:
                await conn.execute(query)

    async def with_notifiations_enabled(self) -> list[User]:
        logger.debug("Getting users with notifications enabled")
        async with await self._connection as conn:
            query = f"SELECT * FROM {USERS_TABLE} WHERE notify = TRUE"
            cursor = await conn.execute(query)
            usage_rows = await cursor.fetchall()
            return [User(**row) for row in usage_rows]

    async def should_notify_usage(self, current_usage: float) -> list[User]:
        logger.debug(
            f"Getting users we should notify with current usage at {current_usage}%"
        )
        async with await self._connection as conn:
            query = f"SELECT * FROM {USERS_TABLE} WHERE notify = TRUE AND was_notified = FALSE AND threshold <= ?"
            cursor = await conn.execute(query, (math.floor(current_usage),))
            usage_rows = await cursor.fetchall()
            return [User(**row) for row in usage_rows]

    async def _query_stats(
        self,
        where: str = "",
        params: Optional[Iterable] = None,
        limit: Optional[int] = None,
    ) -> list[NetUsage]:
        query = f"SELECT * FROM {USAGE_TABLE}"
        if where:
            query = f"{query} {where}"
        query = f"{query} ORDER BY year_month DESC"
        if limit:
            query = f"{query} LIMIT {limit}"
        async with await self._connection as conn:
            cursor = await conn.execute(query, params)
            usage_rows = await cursor.fetchall()
            stats = [NetUsage(**row) for row in usage_rows]
            logger.debug(f"Got {len(stats)} NetUsage records from DB")
            return stats

    async def stats(self, limit: Optional[int] = None) -> list[NetUsage]:
        logger.debug("Getting net usage records")
        return await self._query_stats(limit=limit)

    async def stats_since(self, since: date) -> list[NetUsage]:
        since_str = since.strftime("%Y-%m")
        logger.debug(f"Getting net usage records since {since_str}")
        return await self._query_stats(
            where=f"WHERE year_month >= ?", params=(since_str,)
        )

    async def last_usage(self) -> Optional[NetUsage]:
        logger.debug("Getting latest net usage record")
        async with await self._connection as conn:
            query = f"SELECT * FROM {USAGE_TABLE} ORDER BY year_month DESC LIMIT 1"
            cursor = await conn.execute(query)
            usage = await cursor.fetchone()
            return NetUsage(**usage) if usage else None

    async def create_usage_record(self, usage: BandwidthUsage):
        logger.debug(f"Creating new usage record from {usage}")
        year_month = YearMonth.today()
        async with await self._connection as conn:
            query = (
                f"INSERT INTO {USAGE_TABLE}(year_month, quota, used) VALUES(?, ?, ?)"
            )
            params = (str(year_month), usage.quota, usage.used)
            async with conn:
                await conn.execute(query, params)

    async def update_usage(self, record_id: int, usage: BandwidthUsage):
        logger.debug(f"Updatig usage to {usage} for record with id = {record_id}")
        async with await self._connection as conn:
            query = f"UPDATE {USAGE_TABLE} SET quota = ?, used = ? WHERE id = ?"
            async with conn:
                await conn.execute(query, (usage.quota, usage.used, record_id))
