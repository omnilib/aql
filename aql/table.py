# Copyright 2019 John Reese
# Licensed under the MIT license

from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Sequence,
    Set,
    Type,
    TypeVar,
    get_type_hints,
    overload,
)

from attr import dataclass

from .column import Column
from .errors import AqlError, DuplicateColumnName
from .query import Query
from .types import Comparison

T = TypeVar("T")


class Table(Generic[T]):
    """Table specification using custom columns and a source type."""

    def __init__(
        self, name: str, columns: Sequence[Column], source: Type[T] = None
    ) -> None:
        self._name = name
        self._columns: Sequence[Column] = list(columns)
        self._column_names: Set[str] = set()
        self._source: Optional[Type[T]] = source

        for column in columns:
            if column.name in self._column_names:
                raise DuplicateColumnName(
                    f"column {column.name} already exists in {self._name}"
                )

            self._column_names.add(column.name)
            self.__dict__[column.name] = column

    def __repr__(self) -> str:
        return f"<Table: {self._name}>"

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        """Enable instantiating individual rows from the original source type."""
        if self._source is None:
            raise AqlError(f"No source specified for table {self._name}, cannot call")
        return self._source(*args, **kwargs)  # type: ignore

    def __contains__(self, name) -> bool:
        """Check if columns exist by name."""
        return name in self._column_names

    def __getitem__(self, name) -> Column:
        """Subscripts also return columns."""
        if name in self._column_names:
            return self.__dict__[name]
        else:
            raise KeyError(f"no column {name}")

    def insert(self, *columns: Column) -> Query:
        """Shortcut for Query(<table>).insert()"""
        return Query(self).insert(*columns)

    def select(self, *columns: Column) -> Query:
        """Shortcut for Query(<table>).select()"""
        return Query(self).select(*columns)

    def update(self, *comps: Comparison, **values: Any) -> Query:
        """Shortcut for Query(<table>).update()"""
        return Query(self).update(*comps, **values)

    def delete(self) -> Query:
        """Shortcut for Query(<table>).delete()"""
        return Query(self).delete()


@overload
def table(cls_or_name: Type[T], *args) -> Table[T]:
    ...  # pragma: no cover


@overload
def table(cls_or_name: str, *args) -> Callable[[Type[T]], Table[T]]:
    ...  # pragma: no cover


def table(cls_or_name, *args):
    """Simple decorator to generate table spec from annotated class def."""

    if isinstance(cls_or_name, str):
        table_name = cls_or_name
    else:
        table_name = cls_or_name.__name__

    def wrapper(cls: Type[T]) -> Table[T]:
        columns = []
        for key, value in get_type_hints(cls).items():
            columns.append(Column(key, ctype=value, table_name=table_name))

        if cls.__bases__ == (object,):
            cls = dataclass(cls)

        return Table(table_name, columns=columns, source=cls)

    if isinstance(cls_or_name, str):
        return wrapper
    else:
        return wrapper(cls_or_name)
