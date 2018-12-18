# Copyright 2018 John Reese
# Licensed under the MIT license

from typing import NamedTuple
from unittest import TestCase

from aql.column import Column, Operation
from aql.table import Table, table
from aql.types import Operator


class TableTest(TestCase):
    def test_table_init(self):
        columns = [Column("a"), Column("b"), Column("foo"), Column("bar")]

        tbl = Table("test", columns)
        self.assertEqual(tbl._name, "test")
        self.assertIn("a", tbl._column_names)
        for col, tcol in zip(columns, tbl._columns):
            self.assertIs(col, tcol)
            self.assertIs(col, getattr(tbl, col.name))

        self.assertEqual(tbl.foo == 5, Operation(columns[2], Operator.eq, 5))

    def test_table_decorator_basic(self):
        @table
        class Foo:
            a: int
            b: str

        self.assertIsInstance(Foo, Table)
        self.assertIsInstance(Foo.a, Column)
        self.assertIsInstance(Foo.b, Column)

        foo = Foo(a=1, b="bar")
        self.assertIsInstance(foo, Foo._source)
        self.assertEqual(foo.a, 1)
        self.assertEqual(foo.b, "bar")

    def test_table_decorator_namedtuple(self):
        @table
        class Foo(NamedTuple):
            a: int
            b: str

        self.assertIsInstance(Foo, Table)
        self.assertIsInstance(Foo.a, Column)
        self.assertIsInstance(Foo.b, Column)

        foo = Foo(a=1, b="bar")
        self.assertIsInstance(foo, Foo._source)
        self.assertIsInstance(foo, tuple)
        self.assertEqual(foo.a, 1)
        self.assertEqual(foo.b, "bar")
