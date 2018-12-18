# Copyright 2018 John Reese
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

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        """Enable instantiating individual rows from the original source type."""
        if self._source is None:
            raise AqlError(f"No source specified for table {self._name}, cannot call")
        return self._source(*args, **kwargs)  # type: ignore


@overload
def table(cls_or_name: Type[T], *args) -> Table[T]:
    ...


@overload
def table(cls_or_name: str, *args) -> Callable[[Type[T]], Table[T]]:
    ...


def table(cls_or_name, *args):
    """Simple decorator to generate table spec from annotated class def."""

    if isinstance(cls_or_name, str):
        name = cls_or_name
    else:
        name = cls_or_name.__name__

    def wrapper(cls: Type[T]) -> Table[T]:
        columns = []
        for key, value in get_type_hints(cls).items():
            columns.append(Column(key, ctype=value))

        if cls.__bases__ == (object,):
            cls = dataclass(cls)

        return Table(name, columns=columns, source=cls)

    if isinstance(cls_or_name, str):
        return wrapper
    else:
        return wrapper(cls_or_name)
