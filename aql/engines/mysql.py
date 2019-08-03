# Copyright 2019 John Reese
# Licensed under the MIT license

from typing import Any, List

from ..column import NO_DEFAULT, Primary, Unique
from ..errors import BuildError
from ..query import PreparedQuery, Query
from .sql import SqlEngine, T


class MysqlEngine(SqlEngine, name="mysql"):
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
            parts = [f"`{column.name}`", self.TYPES[ctype.root]]

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
                parts.append(f"`{con._name}`")
            columns = ", ".join(f"`{c}`" for c in con._columns)
            parts.append(f"({columns})")

            column_defs.append(" ".join(parts))

        ine = "IF NOT EXISTS " if query._if_not_exists else ""
        sql = f"CREATE TABLE {ine}`{query.table._name}` ({', '.join(column_defs)})"
        parameters: List[Any] = []
        return PreparedQuery(query.table, sql, parameters)
