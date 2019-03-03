# Copyright 2018 John Reese
# Licensed under the MIT license

import logging
import re
from typing import Dict, Pattern, Type, TypeVar

from ..query import PreparedQuery, Query

LOG = logging.getLogger(__name__)
T = TypeVar("T")


class Engine:
    _engines: Dict[str, Type["Engine"]] = {}
    _uri_regex: Pattern = re.compile(r"(?P<engine>\w+)://(?P<location>.+)")

    def __init__(self, location: str):
        self.name = self.__class__.__name__
        self.location = location

    def __init_subclass__(cls, name, **kwargs):
        super().__init_subclass__(**kwargs)
        name = name.lower()
        if name not in Engine._engines:
            Engine._engines[name] = cls
        else:
            LOG.warning('duplicate engine name "%s" from %s', name, cls)

    @classmethod
    def get_engine(cls, uri: str) -> "Engine":
        """Given a URI matching <engine>://<location>, return an Engine."""
        match = cls._uri_regex.match(uri)
        if not match:
            raise ValueError(
                "invalid engine URI - must follow form '<engine>://<location>'"
            )
        engine, location = match.groups()
        if engine not in cls._engines:
            raise ValueError(f"engine {engine} not found")
        return cls._engines[engine](location)

    def prepare(self, query: Query[T]) -> PreparedQuery[T]:
        """
        Given a query, generate the full SQL query and all parameters.

        Default behavior is to call the method on the engine class corresponding
        to the query action.
        """
        action = query._action.name
        fn = getattr(self, action, None)

        if fn is None:
            raise NotImplementedError(f"{self.name} does not support {action} queries")
        else:
            return fn(query)

    def connect(self) -> "Connection":
        """Create a fresh connection to the specified database."""
        raise NotImplementedError()


class Connection:
    def __init__(self, engine: Engine):
        self._autocommit = False
        self.engine = engine

    def __aenter__(self) -> "Connection":
        raise NotImplementedError()

    def __aexit__(self, *args) -> None:
        pass

    @property
    def autocommit(self) -> bool:
        return self._autocommit

    @autocommit.setter
    def autocommit(self, value: bool) -> None:
        self._autocommit = value

    async def begin(self) -> None:
        """Begin a new transaction."""
        raise NotImplementedError()

    async def commit(self) -> None:
        raise NotImplementedError()

    async def execute(self, query: Query[T]) -> None:
        raise NotImplementedError()

    async def prepare(self, query: Query[T]) -> PreparedQuery[T]:
        return self.engine.prepare(query)
