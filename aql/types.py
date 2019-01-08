# Copyright 2018 John Reese
# Licensed under the MIT license

from enum import Enum, IntEnum, auto
from typing import TYPE_CHECKING, Any, Generic, List, TypeVar, Union

from attr import Factory, dataclass

if TYPE_CHECKING:
    from .column import Column
    from .table import Table

T = TypeVar("T")


class QueryAction(IntEnum):
    unset = 0
    insert = 1
    select = 2
    update = 3
    delete = 4


class Operator(Enum):
    eq = auto()
    ne = auto()
    gt = auto()
    ge = auto()
    lt = auto()
    le = auto()

    in_ = auto()
    like = auto()
    ilike = auto()


class Boolean(Enum):
    and_ = "and"
    or_ = "or"


class Select(IntEnum):
    all = 0
    distinct = 1


class Join(IntEnum):
    inner = 0
    straight = 1
    left = 2
    right = 3


@dataclass
class Comparison:
    column: "Column"
    operator: Operator
    value: Any


Clause = Union[Comparison, "And", "Or"]


class And:
    def __init__(self, *clauses: Clause):
        self.clauses = clauses


class Or:
    def __init__(self, *clauses: Clause):
        self.clauses = clauses


@dataclass
class TableJoin:
    table: "Table"
    style: Join
    on: List[Clause] = Factory(list)
    using: List["Column"] = Factory(list)


class PrimaryKey(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value


class Unique(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value
