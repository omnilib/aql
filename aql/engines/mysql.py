# Copyright 2020 John Reese
# Licensed under the MIT license

from typing import Any, List

from ..column import NO_DEFAULT, Primary, Unique
from ..errors import BuildError, NoConnection
from ..query import PreparedQuery, Query
from .base import Connection, MissingConnector
from .sql import SqlEngine, T, q

try:
    import aiomysql
except ModuleNotFoundError as e:  # pragma:nocover
    aiomysql = MissingConnector(e)


class MysqlEngine(SqlEngine, name="mysql"):

    PLACEHOLDER = "%s"

    def create(  # pylint:disable=too-many-branches
        self, query: Query[T]
    ) -> PreparedQuery[T]:
        column_defs: List[str] = []
        column_types = query.table._column_types
        for column in query.table._columns:
            ctype = column_types.get(column, None)
            if not ctype:
                raise BuildError(f"No column type found for {column.name}")
            if ctype.root not in self.TYPES:
                raise BuildError(f"Unsupported column type {ctype.root}")
            parts = [q(column.name), self.TYPES[ctype.root]]

            if not ctype.nullable:
                parts.append("NOT")
            parts.append("NULL")
            if column.default is not NO_DEFAULT:
                parts.extend(["DEFAULT", repr(column.default)])

            if ctype.autoincrement:
                parts.append("AUTO_INCREMENT")
            if ctype.constraint == Primary:
                parts.append("PRIMARY")
            elif ctype.constraint == Unique:
                parts.append("UNIQUE")

            column_defs.append(" ".join(parts))

        for con in query.table._indexes:
            if isinstance(con, Primary):
                parts = ["PRIMARY KEY"]
            elif isinstance(con, Unique):
                parts = ["UNIQUE INDEX"]
            else:
                parts = ["INDEX"]
            if con._name:
                parts.append(q(con._name))
            columns = ", ".join(q(c) for c in con._columns)
            parts.append(f"({columns})")

            column_defs.append(" ".join(parts))

        ine = "IF NOT EXISTS " if query._if_not_exists else ""
        sql = f"CREATE TABLE {ine}{q(query.table)} ({', '.join(column_defs)})"
        parameters: List[Any] = []
        return PreparedQuery(query.table, sql, parameters)


class MysqlConnection(Connection, name="mysql", engine=MysqlEngine):
    async def connect(self) -> None:
        self._conn = await aiomysql.connect(
            *self._args,
            host=self.location.host,
            port=self.location.port,
            user=self.location.user,
            password=self.location.password,
            unix_socket=self.location.socket,
            db=self.location.database,
            **self._kwargs,
        )

    async def close(self) -> None:
        """Close the connection."""
        if self._conn:
            self._conn.close()
        else:
            raise NoConnection
