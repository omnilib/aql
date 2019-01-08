# Copyright 2018 John Reese
# Licensed under the MIT license

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from .column import Column, Comparison
from .errors import BuildError
from .types import Boolean, QueryAction, Selector

if TYPE_CHECKING:
    from .table import Table

T = TypeVar("T")
Clause = Union[Comparison, "And", "Or"]
Join = Tuple["Table", Sequence[Clause]]


def start(action: QueryAction) -> Callable:
    """Initialize the query for a given action, ensuring no action has started."""

    def wrapper(fn):
        def wrapped(self, *args, **kwargs):
            if self._action:
                raise BuildError(f"query already started with {self._action.name}")
            self._action = action
            return fn(self, *args, **kwargs)

        return wrapped

    return wrapper


def only(*actions: QueryAction) -> Callable:
    """Ensure the current query has been started with one of the given actions."""
    if not actions:
        actions = tuple(QueryAction)

    def wrapper(fn):
        def wrapped(self, *args, **kwargs):
            if not self._action:
                raise BuildError("query not yet started")
            elif self._action not in actions:
                raise BuildError(f"query {self._action} not supported with this method")
            return fn(self, *args, **kwargs)

        return wrapped

    return wrapper


class And:
    def __init__(self, *clauses: Clause):
        self.clauses = clauses


class Or:
    def __init__(self, *clauses: Clause):
        self.clauses = clauses


class Query(Generic[T]):
    def __init__(self, table: "Table[T]") -> None:
        self.table = table
        self._action: QueryAction = QueryAction.unset
        self._selector: Selector = Selector.all
        self._columns: List[Column] = []
        self._rows: List[Any] = []
        self._joins: List[Join] = []
        self._where: List[Clause] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None

    @start(QueryAction.insert)
    def insert(self, *columns: Column) -> "Query[T]":
        self._columns = list(columns)
        return self

    @start(QueryAction.select)
    def select(self, *columns: Column) -> "Query[T]":
        self._columns = list(columns)
        return self

    @start(QueryAction.update)
    def update(self) -> "Query[T]":
        return self

    @start(QueryAction.delete)
    def delete(self) -> "Query[T]":
        return self

    @only(QueryAction.select)
    def distinct(self) -> "Query[T]":
        self._selector = Selector.distinct
        return self

    @only(QueryAction.insert)
    def values(self, *rows) -> "Query[T]":
        self._rows = list(rows)
        return self

    @only(QueryAction.select)
    def join(self, table: "Table", *on: Clause) -> "Query[T]":
        self._joins.append((table, on))
        return self

    @only(QueryAction.select, QueryAction.update, QueryAction.delete)
    def where(self, *clauses: Clause, grouping=Boolean.and_) -> "Query[T]":
        if not clauses:
            raise ValueError("no criteria specified for where clause")
        elif len(clauses) > 1:
            self._where.append(
                And(*clauses) if grouping == Boolean.and_ else Or(*clauses)
            )
        else:
            self._where.extend(clauses)
        return self

    @only()
    def limit(self, n: int, offset: int = None) -> "Query[T]":
        self._limit = n
        self._offset = offset
        return self

    @only()
    def offset(self, n: int) -> "Query[T]":
        self._offset = n
        return self
