# Copyright 2018 John Reese
# Licensed under the MIT license

from ..query import PreparedQuery, Query
from .base import Connection, Engine, T


class SqliteEngine(Engine, name="sqlite"):
    def prepare(self, query: Query[T]) -> PreparedQuery[T]:
        pass
