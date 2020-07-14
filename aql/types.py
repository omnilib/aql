# Copyright 2020 John Reese
# Licensed under the MIT license

from enum import Enum, IntEnum, auto
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    List,
    NewType,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from attr import Factory, dataclass

if TYPE_CHECKING:  # pragma: no cover
    from .column import Column
    from .table import Table

T = TypeVar("T")


@dataclass
class Location:
    """
    Database connection information
    """

    engine: str
    socket: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None


# Custom types for longer string/byte columns
Text = NewType("Text", str)
Blob = NewType("Blob", bytes)


class QueryAction(IntEnum):
    unset = auto()
    create = auto()
    insert = auto()
    select = auto()
    update = auto()
    delete = auto()


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
    inner = auto()
    left = auto()
    right = auto()


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


SqlParams = Tuple[str, List[Any]]


class PrimaryKey(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value


class Unique(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value
