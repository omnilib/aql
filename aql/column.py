# Copyright 2020 John Reese
# Licensed under the MIT license

from typing import Any, Generic, Optional, Sequence, Type, TypeVar, Union

from attr import dataclass

from .errors import InvalidColumnType
from .types import Comparison, Operator

NO_DEFAULT = object()
T = TypeVar("T")


class AutoIncrement(Generic[T]):
    pass


class Index(Generic[T]):
    _AUTO_PREFIX = "idx"

    def __init__(self, *columns: str, name: Optional[str] = None):
        self._columns = list(columns)
        if name is not None:
            self._name = name
        else:
            names = [self._AUTO_PREFIX] + list(columns)
            self._name = "_".join(names)

    def __eq__(self, other):
        return (
            type(self) == type(other)  # pylint:disable=unidiomatic-typecheck
            and self._columns == other._columns
        )


class Unique(Index[T]):
    _AUTO_PREFIX = "unq"


class Primary(Index[T]):
    _AUTO_PREFIX = "pri"


@dataclass
class ColumnType:
    root: Optional[Type]
    nullable: bool = False
    autoincrement: bool = False
    constraint: Optional[Type[Index]] = None

    @staticmethod
    def parse(t: Type) -> "ColumnType":
        ctype = ColumnType(None)

        while hasattr(t, "__origin__"):
            origin = t.__origin__
            args = list(t.__args__)

            if origin is Union:
                if type(None) in args:  # pylint:disable=unidiomatic-typecheck
                    ctype.nullable = True
                    args.remove(type(None))
            elif origin is AutoIncrement:
                ctype.autoincrement = True
            elif issubclass(origin, Index):
                if ctype.constraint:
                    raise InvalidColumnType(f"Unsupported double constraint: {t}")
                ctype.constraint = origin
            else:
                raise InvalidColumnType(f"Unsupported type origin {origin}")

            if len(args) > 1:
                raise InvalidColumnType(f"Unsupported union type: {args}")

            t = args[0]

        ctype.root = t

        if ctype.autoincrement and ctype.root != int:
            raise InvalidColumnType(f"Autoincrement not supported with {ctype.root}")

        return ctype


class Column:
    def __init__(
        self,
        name: str,
        ctype: Type = None,
        default: Any = NO_DEFAULT,
        table_name: str = "",
    ) -> None:
        self.name = name
        self.ctype = ctype
        self.default = default
        self.table_name = table_name

    def __repr__(self) -> str:
        return f"<Column: {self.full_name}>"

    def __hash__(self) -> int:
        return hash((self.name, self.ctype, self.default, self.table_name))

    @property
    def full_name(self) -> str:
        return f"{self.table_name}.{self.name}" if self.table_name else self.name

    def in_(self, values: Sequence[Any]) -> Comparison:
        return Comparison(self, Operator.in_, list(values))

    def like(self, value: str) -> Comparison:
        return Comparison(self, Operator.like, value)

    def ilike(self, value: str) -> Comparison:
        return Comparison(self, Operator.ilike, value)

    def __eq__(self, value: Any) -> Comparison:  # type: ignore
        return Comparison(self, Operator.eq, value)

    def __ne__(self, value: Any) -> Comparison:  # type: ignore
        return Comparison(self, Operator.ne, value)

    def __gt__(self, value: Any) -> Comparison:
        return Comparison(self, Operator.gt, value)

    def __ge__(self, value: Any) -> Comparison:
        return Comparison(self, Operator.ge, value)

    def __lt__(self, value: Any) -> Comparison:
        return Comparison(self, Operator.lt, value)

    def __le__(self, value: Any) -> Comparison:
        return Comparison(self, Operator.le, value)
