# Copyright 2018 John Reese
# Licensed under the MIT license

from ..query import PreparedQuery, Query
from .base import Engine, T


class SqlEngine(Engine, name="sql"):
    """Generic SQL engine for generating standardized queries."""

    def __init__(self, location: str, placeholder: str = "?"):
        super().__init__(location)
        self.placeholder = placeholder

    def prepare(self, query: Query[T]) -> PreparedQuery[T]:
        pass
