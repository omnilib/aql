# Copyright 2019 John Reese
# Licensed under the MIT license

from .sql import SqlEngine


class SqliteEngine(SqlEngine, name="sqlite"):
    """Engine/connector for sqlite databases using aiosqlite."""
