# Copyright 2019 John Reese
# Licensed under the MIT license

from typing import Optional, TypeVar

from ..query import Query
from .base import Connection, Cursor, MissingConnector
from .sql import SqlEngine  # pylint: disable=unused-import

try:
    import aiosqlite
except ModuleNotFoundError as e:
    aiosqlite = MissingConnector(e)

T = TypeVar("T")


class SqliteCursor(Cursor):
    def __init__(self, conn: Connection, cursor: Optional["aiosqlite.Cursor"]):
        super().__init__(conn)
        self._cursor = cursor

    def __getattr__(self, key):
        return getattr(self._cursor, key)


class SqliteConnection(Connection, name="sqlite", engine=SqlEngine):
    async def connect(self) -> None:
        """Initiate the connection, and close when exited."""
        self._conn = await aiosqlite.connect(self.location, *self._args, **self._kwargs)

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    async def query(self, query: Query[T]) -> Cursor:
        prepared = self.engine.prepare(query)
        cursor = await self._conn.execute(prepared.sql, prepared.parameters)
        return SqliteCursor(self, cursor)
