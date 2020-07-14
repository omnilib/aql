# Copyright 2020 John Reese
# Licensed under the MIT license

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    get_type_hints,
    overload,
)

from attr import NOTHING, dataclass, fields_dict

from .column import NO_DEFAULT, Column, ColumnType, Index
from .errors import AqlError, DuplicateColumnName
from .query import Query
from .types import Comparison

T = TypeVar("T")


class Table(Generic[T]):
    """Table specification using custom columns and a source type."""

    def __init__(
        self, name: str, cons: Iterable[Union[Column, Index]], source: Type[T] = None
    ) -> None:
        self._name = name
        self._columns: List[Column] = []
        self._column_names: Set[str] = set()
        self._column_types: Dict[Column, ColumnType] = {}
        self._indexes: List[Index] = []
        self._source: Optional[Type[T]] = source

        for con in cons:
            if isinstance(con, Column):
                if con.name in self._column_names:
                    raise DuplicateColumnName(
                        f"column {con.name} already exists in {self._name}"
                    )
                self._columns.append(con)
                self._column_names.add(con.name)
                self.__dict__[con.name] = con

                if not con.ctype:
                    continue

                ctype = ColumnType.parse(con.ctype)
                if ctype.constraint and ctype.constraint == Index:
                    self._indexes.append(ctype.constraint(con.name))
                self._column_types[con] = ctype

            elif isinstance(con, Index):
                self._indexes.append(con)

            else:
                raise ValueError("Unexpected constraint")

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

    def create(self, if_not_exists: bool = False) -> Query:
        """Shortcut for Query(<table>).create()"""
        return Query(self).create(if_not_exists=if_not_exists)

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
def table(cls_or_name: Type[T], *args: Index) -> Table[T]:
    ...  # pragma: no cover


@overload
def table(cls_or_name: str, *args: Index) -> Callable[[Type[T]], Table[T]]:
    ...  # pragma: no cover


@overload
def table(cls_or_name: Index, *args: Index) -> Callable[[Type[T]], Table[T]]:
    ...  # pragma: no cover


def table(cls_or_name, *args: Index):
    """Simple decorator to generate table spec from annotated class def."""

    table_name: Optional[str] = None
    if isinstance(cls_or_name, str):
        table_name = cls_or_name
    elif isinstance(cls_or_name, Index):
        args = (cls_or_name, *args)
    else:
        table_name = cls_or_name.__name__

    def wrapper(cls: Type[T]) -> Table[T]:
        name = table_name or cls.__name__

        if cls.__bases__ == (object,):
            cls = dataclass(cls)

        cons: List[Union[Column, Index]] = list(args)
        if issubclass(cls, tuple):
            defaults = getattr(cls, "_field_defaults", {})
        else:
            defaults = {
                k: (NO_DEFAULT if a.default == NOTHING else a.default)
                for k, a in fields_dict(cls).items()
            }
        for key, value in get_type_hints(cls).items():
            cons.append(
                Column(
                    key,
                    ctype=value,
                    table_name=name,
                    default=defaults.get(key, NO_DEFAULT),
                )
            )

        return Table(name, cons=cons, source=cls)

    if isinstance(cls_or_name, (str, Index)):
        return wrapper
    else:
        return wrapper(cls_or_name)
