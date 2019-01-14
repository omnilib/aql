# Copyright 2018 John Reese
# Licensed under the MIT license

from itertools import chain

from attr import astuple

from ..query import PreparedQuery, Query
from .base import Engine, T


class SqlEngine(Engine, name="sql"):
    """Generic SQL engine for generating standardized queries."""

    def __init__(self, location: str, placeholder: str = "?"):
        super().__init__(location)
        self.placeholder = placeholder

    def insert(self, query: Query[T]) -> PreparedQuery[T]:
        columns = ", ".join(f"`{column.full_name}`" for column in query._columns)
        rows = [astuple(row) for row in query._rows]
        values = ", ".join(
            f"({','.join(self.placeholder for _ in row)})" for row in rows
        )
        parameters = list(chain.from_iterable(rows))
        sql = f"INSERT INTO `{query.table._name}` ({columns}) VALUES {values}"

        return PreparedQuery(query.table, sql, parameters)
