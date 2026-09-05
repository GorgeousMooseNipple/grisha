import logging
import aiosqlite
from utils.config import CONFIG
from pathlib import Path
from typing import Optional, Iterable
from datetime import date

from .model import User, NetUsage


logger = logging.getLogger(__name__)

USERS_TABLE = "users"
USAGE_TABLE = "net_usage"


class DbApi:
    def __init__(self):
        self.db_path = Path(CONFIG.settings.db_path)
        if not self.db_path.parent.exists():
            logger.info(f"Creating DB parent path at '{self.db_path.parent}'")
            self.db_path.parent.mkdir(parents=True)

    async def init_db(self, script_path: str | Path):
        logger.info("Initiating DB")
        script_path = Path(script_path)

        if not script_path.exists():
            raise RuntimeError(
                f"Path to DB init script does not exist at '{script_path}'"
            )

        async with aiosqlite.connect(self.db_path) as conn:
            init_script = script_path.read_text("utf-8")
            await conn.executescript(init_script)

    async def _query_users(
        self, where: str = "", params: Optional[Iterable] = None
    ) -> list[User]:
        query = f"SELECT * FROM {USERS_TABLE}"
        if where:
            query = f"{query} {where}"
        logger.debug(f"Executing {USERS_TABLE} query '{query}'")
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            cursor.row_factory = aiosqlite.Row
            await cursor.execute(query, params)
            user_rows = await cursor.fetchall()
            users = [User(**row) for row in user_rows]
            logger.debug(f"Got {len(users)} User records from DB")
            return users

    async def users(self) -> list[User]:
        return await self._query_users()

    async def users_with_notification(self) -> list[User]:
        return await self._query_users("WHERE notify = TRUE")

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
        logger.debug(f"Executing {USAGE_TABLE} query '{query}'")
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            cursor.row_factory = aiosqlite.Row
            await cursor.execute(query, params)
            usage_rows = await cursor.fetchall()
            stats = [NetUsage(**row) for row in usage_rows]
            logger.debug(f"Got {len(stats)} NetUsage records from DB")
            return stats

    async def stats(self, limit: Optional[int] = None) -> list[NetUsage]:
        return await self._query_stats(limit=limit)

    async def stats_since(self, since: date) -> list[NetUsage]:
        since_str = since.strftime("%Y-%m")
        return await self._query_stats(
            where=f"WHERE year_month >= ?", params=(since_str,)
        )

    async def insert_user(self, user: User):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                f"INSERT INTO {USERS_TABLE}(id, username, name, notify, threshold) VALUES(?, ?, ?, ?, ?)",
                (user.id, user.username, user.name, user.notify, user.threshold),
            )
            await conn.commit()

    async def user_by_id(self, id: int) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            cursor.row_factory = aiosqlite.Row
            query = f"SELECT * FROM {USERS_TABLE} WHERE id = ?"
            logger.debug(f"Executing query '{query}'")
            await cursor.execute(query, (id,))
            user = await cursor.fetchone()
            return User(**user) if user else None

    async def set_threshold(self, user_id: int, threshold: int):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            query = f"UPDATE {USERS_TABLE} SET threshold = ? WHERE id = ?"
            logger.debug(f"Executing query: '{query}'")
            await cursor.execute(query, (threshold, user_id))
            await conn.commit()

    async def _set_notifications(self, user_id: int, enable: bool):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            query = f"UPDATE {USERS_TABLE} SET notify = ? WHERE id = ?"
            logger.debug(f"Executing query: '{query}'")
            await cursor.execute(query, (enable, user_id))
            await conn.commit()

    async def enable_notifications(self, user_id: int):
        await self._set_notifications(user_id, enable=True)

    async def disable_notifications(self, user_id: int):
        await self._set_notifications(user_id, enable=False)

    async def should_notify(self, current_usage: float) -> list[User]:
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            cursor.row_factory = aiosqlite.Row
            query = (
                f"SELECT * FROM {USERS_TABLE} WHERE notify = TRUE AND threshold <= ?"
            )
            logger.debug(
                f"Executing query '{query}' with current usage at {current_usage}"
            )
            await cursor.execute(query, (round(current_usage),))
            usage_rows = await cursor.fetchall()
            return [User(**row) for row in usage_rows]
