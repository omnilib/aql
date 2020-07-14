# Copyright 2020 John Reese
# Licensed under the MIT license

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

from attr import make_class

from .column import Column
from .errors import BuildError
from .types import (
    And,
    Boolean,
    Clause,
    Comparison,
    Join,
    Operator,
    Or,
    QueryAction,
    Select,
    TableJoin,
)

if TYPE_CHECKING:  # pragma: no cover
    from .table import Table

T = TypeVar("T")


def start(action: QueryAction) -> Callable:
    """Initialize the query for a given action, ensuring no action has started."""

    def wrapper(fn):
        def wrapped(self, *args, **kwargs):
            if self._action != QueryAction.unset:
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
            if self._action == QueryAction.unset:
                raise BuildError("query not yet started")
            elif self._action not in actions:
                raise BuildError(f"query {self._action} not supported with this method")
            return fn(self, *args, **kwargs)

        return wrapped

    return wrapper


class Query(Generic[T]):
    def __init__(self, table: "Table[T]") -> None:
        self.table = table
        self._action: QueryAction = QueryAction.unset
        self._if_not_exists: bool = False
        self._selector: Select = Select.all
        self._columns: List[Column] = []
        self._updates: Dict[Column, Any] = {}
        self._rows: List[Any] = []
        self._joins: List[TableJoin] = []
        self._groupby: List[Column] = []
        self._having: List[Clause] = []
        self._where: List[Clause] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._everything: bool = False

    @start(QueryAction.create)
    def create(self, if_not_exists: bool = False) -> "Query[T]":
        self._if_not_exists = if_not_exists
        return self

    @start(QueryAction.insert)
    def insert(self, *columns: Column) -> "Query[T]":
        self._columns = list(columns or self.table._columns)
        return self

    @start(QueryAction.select)
    def select(self, *columns: Column) -> "Query[T]":
        self._columns = list(columns or self.table._columns)
        return self

    @start(QueryAction.update)
    def update(self, *comps: Comparison, **values: Any) -> "Query[T]":
        if not (comps or values):
            raise BuildError("no update criteria specified")
        for comp in comps:
            if comp.operator != Operator.eq:
                raise BuildError("only equality comparisons allowed in updates")
        self._updates = {
            **{self.table[name]: value for name, value in values.items()},
            **{comp.column: comp.value for comp in comps},
        }
        return self

    @start(QueryAction.delete)
    def delete(self) -> "Query[T]":
        return self

    @only(QueryAction.select)
    def distinct(self) -> "Query[T]":
        self._selector = Select.distinct
        return self

    @only(QueryAction.insert)
    def values(self, *rows) -> "Query[T]":
        self._rows.extend(rows)
        return self

    @only(QueryAction.select)
    def join(self, table: "Table", style: Join = Join.inner) -> "Query[T]":
        self._joins.append(TableJoin(table, style))
        return self

    @only(QueryAction.select)
    def on(self, *on_: Clause) -> "Query[T]":
        join = self._joins[-1]
        if join.using:
            raise BuildError(f"join already specified USING ({join})")
        join.on.extend(on_)
        return self

    @only(QueryAction.select)
    def using(self, *columns: Column) -> "Query[T]":
        join = self._joins[-1]
        if join.on:
            raise BuildError(f"join already specified ON ({join})")
        join.using.extend(columns)
        return self

    @only(QueryAction.select)
    def groupby(self, *columns: Column) -> "Query[T]":
        if self._groupby:
            raise BuildError("group by already specified")
        if not columns:
            raise BuildError("no columns specified for group by clause")
        self._groupby = list(columns)
        return self

    @only(QueryAction.select)
    def having(self, *clauses: Clause, grouping=Boolean.and_) -> "Query[T]":
        if not self._groupby:
            raise BuildError("having must be preceded by group by")
        if not clauses:
            raise BuildError("no criteria specified for having clause")
        self._having.append(And(*clauses) if grouping == Boolean.and_ else Or(*clauses))
        return self

    @only(QueryAction.select, QueryAction.update, QueryAction.delete)
    def where(self, *clauses: Clause, grouping=Boolean.and_) -> "Query[T]":
        if not clauses:
            raise BuildError("no criteria specified for where clause")
        self._where.append(And(*clauses) if grouping == Boolean.and_ else Or(*clauses))
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

    @only(QueryAction.update, QueryAction.delete)
    def everything(self) -> "Query[T]":
        self._everything = True
        return self

    @only(QueryAction.select)
    def factory(self) -> Type:
        if self._columns == self.table._columns and self.table._source:
            return self.table._source
        return make_class(
            "Row", [col.name for col in self._columns], slots=True, frozen=True
        )


class PreparedQuery(Generic[T]):
    def __init__(self, table: "Table[T]", sql: str, parameters: Sequence[Any]):
        self.table = table
        self.sql = sql
        self.parameters = parameters

    def __iter__(self):
        """
        Helper method for passing (query, params) to db.execute() or similar.

        Example:
            query = Engine.prepare(...)
            db.execute(*query)  # equivalent to db.execute(query.sql, query.parameters)
        """
        return iter((self.sql, self.parameters))
