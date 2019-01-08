# Copyright 2018 John Reese
# Licensed under the MIT license

from enum import Enum, IntEnum, auto
from typing import Generic, TypeVar

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


class Selector(IntEnum):
    all = 0
    distinct = 1


class PrimaryKey(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value


class Unique(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value
