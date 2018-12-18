# Copyright 2018 John Reese
# Licensed under the MIT license

from typing import Any, Sequence

from .errors import QueryError
from .table import Table
from .types import QueryAction


class Query:
    def __init__(self, table: Table) -> None:
        self.table = table
        self._action: QueryAction = QueryAction.unset
        self._columns: Sequence[Any]
        self._rows: Sequence[Any]

    def insert(self, *columns) -> "Query":
        self._start(QueryAction.insert)
        self._columns = columns
        return self

    def select(self, *columns) -> "Query":
        self._start(QueryAction.select)
        self._columns = columns
        return self

    def update(self, *rows) -> "Query":
        self._start(QueryAction.update)
        self._rows = rows
        return self

    def delete(self) -> "Query":
        self._start(QueryAction.delete)
        return self

    def _start(self, action: QueryAction) -> None:
        """Initialize the query for a given action, ensuring no action has started."""
        if self._action:
            raise QueryError(f"query already started with {self._action.name}")
        self._action = action
