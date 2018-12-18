# Copyright 2018 John Reese
# Licensed under the MIT license

from typing import Any, Sequence, Type

from attr import dataclass

from .types import Operator

NO_DEFAULT = object()


@dataclass
class Operation:
    column: "Column"
    operator: Operator
    value: Any


class Column:
    def __init__(
        self, name: str, ctype: Type = None, default: Any = NO_DEFAULT
    ) -> None:
        self.name = name
        self.ctype = ctype
        self.default = default

    def in_(self, values: Sequence[Any]) -> Operation:
        return Operation(self, Operator.in_, list(values))

    def like(self, value: str) -> Operation:
        return Operation(self, Operator.like, value)

    def ilike(self, value: str) -> Operation:
        return Operation(self, Operator.ilike, value)

    def __eq__(self, value: Any) -> Operation:  # type: ignore
        return Operation(self, Operator.eq, value)

    def __ne__(self, value: Any) -> Operation:  # type: ignore
        return Operation(self, Operator.ne, value)

    def __gt__(self, value: Any) -> Operation:
        return Operation(self, Operator.gt, value)

    def __ge__(self, value: Any) -> Operation:
        return Operation(self, Operator.ge, value)

    def __lt__(self, value: Any) -> Operation:
        return Operation(self, Operator.lt, value)

    def __le__(self, value: Any) -> Operation:
        return Operation(self, Operator.le, value)
