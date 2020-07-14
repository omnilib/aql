# Copyright 2020 John Reese
# Licensed under the MIT license

import logging
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Generator,
    Generic,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from ..column import Column
from ..errors import BuildError, NoConnection, UnknownConnector
from ..query import PreparedQuery, Query
from ..table import Table
from ..types import Location

LOG = logging.getLogger(__name__)
T = TypeVar("T")


def q(t: Union[Table, Column, str]) -> str:
    """Return the backtick quoted table name, column name, or raw string"""
    if isinstance(t, Column):
        return f"`{t.table_name}`.`{t.name}`" if t.table_name else f"`{t.name}`"
    elif isinstance(t, Table):
        return f"`{t._name}`"
    else:
        return f"`{t}`"


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

    def __init__(self, engine: Engine, location: Location, *args: Any, **kwargs: Any):
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
        raise NotImplementedError

    async def close(self) -> None:
        """Close the connection."""
        if self._conn:
            await self._conn.close()
        else:
            raise NoConnection

    @property
    def autocommit(self) -> bool:
        return self._autocommit

    @autocommit.setter
    def autocommit(self, value: bool) -> None:
        self._autocommit = value

    async def begin(self) -> None:
        """Begin a new transaction."""
        await self._conn.begin()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._conn.commit()

    async def rollback(self) -> None:
        """Rollback/cancel the current transaction."""
        await self._conn.rollback()

    async def cursor(self) -> "Cursor":
        """Return a new cursor object."""
        cur = await self._conn.cursor()
        return Cursor(self, cur)

    def execute(self, query: Query[T]) -> "Result[T]":
        """Execute the given query on a new cursor and return the cursor."""
        return Result(query, self)

    # synonyms
    query = execute
    abort = rollback


class Cursor:
    def __init__(self, connection: Connection, cursor: Any):
        self._conn = connection
        self._cursor = cursor
        self._query = None

    def __aiter__(self) -> AsyncIterator[T]:
        """Iterate over rows returned from the previous query."""
        return self

    async def __anext__(self) -> T:
        """Iterate over rows returned from the previous query."""
        row = await self.fetchone()
        if row is None:
            raise StopAsyncIteration
        return row

    def __await__(self) -> Generator[Any, None, Sequence[T]]:
        """Return all rows from previous query."""
        return self.fetchall().__await__()

    async def __aenter__(self) -> "Cursor":
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
        return self._cursor.rowcount

    @property
    def last_id(self) -> Optional[int]:
        """ID of last modified row, or None if not available."""
        raise self._cursor.lastrowid

    def convert(self, row) -> T:
        """Convert from the cursor's native data type to the query object type."""
        if self._query:
            return self._query.table(row)
        else:
            return row

    async def close(self) -> None:
        """Close the cursor."""
        await self._cursor.close()

    async def execute(self, query: str, parameters: Any = None) -> None:
        """Execute the given query with this cursor."""
        await self._cursor.execute(query, parameters)

    async def fetchone(self) -> Optional[Any]:
        """Return the next row from the previous query, or None when exhausted."""
        return await self._cursor.fetchone()

    async def fetchall(self) -> Sequence[Any]:
        """Return all rows from the previous query."""
        return await self._cursor.fetchall()

    # synonyms
    query = execute


class Result(Generic[T]):
    """
    Lazy awaitable or async-iterable object that runs the query once awaited.

    Awaiting the result object will fetch and convert all rows to appropriate objects.
    Iterating the result will fetch and convert individual rows at a time.

    Examples::

        result = db.execute(Foo.select())
        # query not yet executed
        rows = await result
        # query executed and any resulting rows returned
        print(result.row_count)

        async for row in db.execute(Foo.select()):
            ...

        rows = await db.execute(Foo.select())

    """

    def __init__(self, query: Query[T], connection: Connection):
        self.query = query
        self.connection = connection
        self._cursor: Optional[Cursor] = None
        self._started = False
        self.factory: Optional[Type[T]] = None

    def __await__(self) -> Generator[Any, None, Sequence[T]]:
        return self.rows().__await__()

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        row = await self.row()
        if row is None:
            raise StopAsyncIteration
        return row

    @property
    def row_count(self) -> int:
        """Number of rows affected by previous query."""
        if self._cursor is None:
            return 0
        return self._cursor.row_count

    @property
    def last_id(self) -> Optional[int]:
        """ID of last modified row, or None if not available."""
        if self._cursor is None:
            return None
        return self._cursor.last_id

    async def run(self) -> Cursor:
        if self._cursor:
            return self._cursor

        try:
            self.factory = self.query.factory()
        except BuildError:
            pass

        self._cursor = await self.connection.cursor()
        prepared = self.connection.engine.prepare(self.query)
        await self._cursor.execute(prepared.sql, prepared.parameters)
        return self._cursor

    async def row(self) -> Optional[T]:
        cursor = await self.run()
        row = await cursor.fetchone()
        if self.factory:
            return self.factory(*row)
        return None

    async def rows(self) -> Sequence[T]:
        cursor = await self.run()
        rows = await cursor.fetchall()
        if self.factory:
            return [self.factory(*row) for row in rows]
        else:
            return rows
