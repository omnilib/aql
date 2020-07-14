# Copyright 2020 John Reese
# Licensed under the MIT license

import logging
from typing import Any, List, TypeVar

from ..column import NO_DEFAULT, Primary, Unique
from ..errors import BuildError
from ..query import PreparedQuery, Query
from .base import Connection, MissingConnector
from .sql import SqlEngine, q

try:
    import aiosqlite
except ModuleNotFoundError as e:  # pragma:nocover
    aiosqlite = MissingConnector(e)

LOG = logging.getLogger(__name__)
T = TypeVar("T")


class SqliteEngine(SqlEngine, name="sqlite"):
    def create(self, query: Query[T]) -> PreparedQuery[T]:
        column_defs: List[str] = []
        column_types = query.table._column_types
        for column in query.table._columns:
            ctype = column_types.get(column, None)
            if not ctype:
                raise BuildError(f"No column type found for {column.name}")
            if ctype.root not in self.TYPES:
                raise BuildError(f"Unsupported column type {ctype.root}")
            parts = [q(column.name), self.TYPES[ctype.root]]

            if ctype.constraint == Primary:
                parts.append("PRIMARY KEY")
            elif ctype.constraint == Unique:
                parts.append("UNIQUE")
            if ctype.autoincrement:
                parts.append("AUTOINCREMENT")

            if not ctype.nullable:
                parts.append("NOT NULL")
            if column.default is not NO_DEFAULT:
                parts.extend(["DEFAULT", repr(column.default)])

            column_defs.append(" ".join(parts))

        for con in query.table._indexes:
            if isinstance(con, Primary):
                parts = ["PRIMARY KEY"]
            elif isinstance(con, Unique):
                parts = ["UNIQUE"]
            else:
                continue  # pragma:nocover
            columns = ", ".join(q(c) for c in con._columns)
            parts.append(f"({columns})")

            column_defs.append(" ".join(parts))

        ine = "IF NOT EXISTS " if query._if_not_exists else ""
        sql = f"CREATE TABLE {ine}{q(query.table)} ({', '.join(column_defs)})"
        parameters: List[Any] = []
        return PreparedQuery(query.table, sql, parameters)


class SqliteConnection(Connection, name="sqlite", engine=SqliteEngine):
    async def connect(self) -> None:
        """Initiate the connection, and close when exited."""
        self._conn = await aiosqlite.connect(
            self.location.database, *self._args, **self._kwargs
        )

    @property
    def autocommit(self) -> bool:
        return self._conn.isolation_level is None

    @autocommit.setter
    def autocommit(self, value: bool) -> None:
        self._conn.isolation_level = None if value else "DEFERRED"

    async def begin(self) -> None:
        await self._conn.execute("BEGIN TRANSACTION")
