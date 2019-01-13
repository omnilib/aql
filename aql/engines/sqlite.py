# Copyright 2018 John Reese
# Licensed under the MIT license

from ..query import PreparedQuery, Query
from .base import Connection, T
from .sql import SqlEngine


class SqliteEngine(SqlEngine, name="sqlite"):
    """Engine/connector for sqlite databases using aiosqlite."""
