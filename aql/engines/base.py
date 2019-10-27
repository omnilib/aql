# Copyright 2019 John Reese
# Licensed under the MIT license

import logging
import re
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Generator,
    Optional,
    Pattern,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

from ..errors import UnknownConnector
from ..query import PreparedQuery, Query

LOG = logging.getLogger(__name__)
T = TypeVar("T")


class MissingConnector:
    __slots__ = ["_error_"]

    def __init__(self, error: Exception):
        self._error_ = error

    def __getattr__(self, key: str) -> Any:
        raise Exception("Dependency missing") from self._error_


class Engine:
    _engines: Dict[str, Type["Engine"]] = {}

    def __init__(self):
        self.name = self.__class__.__name__

    def __init_subclass__(cls, name: str) -> None:
        super().__init_subclass__()
        name = name.lower()
        if name not in Engine._engines:
            Engine._engines[name] = cls
        else:
            LOG.warning('duplicate engine name "%s" from %s', name, cls)

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


class Connection:
    _connectors: Dict[str, Tuple[Type["Connection"], Type[Engine]]] = {}
    _uri_regex: Pattern = re.compile(r"(?P<engine>\w+)://(?P<location>.+)")

    def __init__(self, engine: Engine, location: str, *args: Any, **kwargs: Any):
        self._conn: Any = None
        self._autocommit = False
        self._args = args
        self._kwargs = kwargs
        self.engine = engine
        self.location = location

    def __init_subclass__(cls, name: str, engine: Type[Engine], **kwargs):
        super().__init_subclass__()
        name = name.lower()
        if name not in Connection._connectors:
            Connection._connectors[name] = (cls, engine)
        else:
            LOG.warning('duplicate engine name "%s" from %s', name, cls)

    @classmethod
    def get_connector(cls, name: str) -> Tuple[Type["Connection"], Type[Engine]]:
        """Given a name, get a connector class."""
        if name not in cls._connectors:
            raise UnknownConnector(f"Connector {name} not registered")
        kls, engine = cls._connectors[name]
        return kls, engine

    async def __aenter__(self) -> "Connection":
        """Initiate the connection, and close when exited."""
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        """Complete the connection."""
        await self.close()

    async def connect(self) -> None:
        """Initiate the connection."""

    async def close(self) -> None:
        """Close the connection."""

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
        """Commit the current transaction."""
        raise NotImplementedError()

    async def abort(self) -> None:
        """Abort/cancel the current transaction."""
        raise NotImplementedError()

    def cursor(self) -> "Cursor":
        """Return a new cursor object."""
        raise NotImplementedError()

    async def query(self, query: Query[T]) -> "Cursor":
        """Execute the given query on a new cursor and return the cursor."""
        raise NotImplementedError()


class Cursor:
    def __init__(self, connection: Connection):
        self._conn = connection

    def __aiter__(self) -> AsyncIterator[T]:
        """Iterate over rows returned from the previous query."""
        return self

    async def __anext__(self) -> T:
        """Iterate over rows returned from the previous query."""
        row = await self.row()
        if row is None:
            raise StopAsyncIteration
        return row

    def __await__(self) -> Generator[Any, None, Sequence[T]]:
        """Return all rows from previous query."""
        return self.rows().__await__()

    async def __aenter__(self) -> "Cursor":
        """Close the cursor when exited."""
        return self

    async def __aexit__(self, *args) -> None:
        """Close the cursor when exited."""
        await self.close()

    @property
    def connection(self) -> Connection:
        """Return the associated connection object."""
        return self._conn

    @property
    def row_count(self) -> int:
        """Number of rows affected by previous query."""
        raise NotImplementedError()

    @property
    def last_id(self) -> Optional[int]:
        """ID of last modified row, or None if not available."""
        raise NotImplementedError()

    async def close(self) -> None:
        """Close the cursor."""
        return

    async def execute(self, query: Query[T]) -> None:
        """Execute the given query with this cursor."""
        raise NotImplementedError()

    async def row(self) -> Optional[T]:
        """Return the next row from the previous query, or None when exhausted."""
        raise NotImplementedError()

    async def rows(self) -> Sequence[T]:
        """Return all rows from the previous query."""
        raise NotImplementedError()
