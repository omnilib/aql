# Copyright 2019 John Reese
# Licensed under the MIT license

from typing import NamedTuple
from unittest import TestCase

from aql.column import Column, Comparison
from aql.errors import AqlError, DuplicateColumnName
from aql.query import Query
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

        self.assertEqual(tbl.foo == 5, Comparison(columns[2], Operator.eq, 5))
        self.assertTrue("a" in tbl)
        self.assertFalse("z" in tbl)
        self.assertEqual(tbl["a"], columns[0])

        with self.assertRaises(KeyError):
            tbl["z"]

        with self.assertRaises(DuplicateColumnName):
            Table("test", columns + columns[:1])

    def test_table_call(self):
        class Foo:
            a: int
            b: str

        Bar = table(Foo)
        self.assertEqual(Foo(1, ""), Bar(1, ""))

        columns = [Column("a"), Column("b"), Column("foo"), Column("bar")]
        Tbl = Table("test", columns)

        with self.assertRaises(AqlError):
            Tbl(1, 2, 3, 4)

    def test_table_decorator_basic(self):
        @table("foo")
        class Foo:
            a: int
            b: str

        self.assertIsInstance(Foo, Table)
        self.assertIsInstance(Foo.a, Column)
        self.assertIsInstance(Foo.b, Column)
        self.assertEqual(Foo._name, "foo")
        self.assertEqual(Foo._columns, [Foo.a, Foo.b])

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

    def test_table_helpers(self):
        @table
        class Foo(NamedTuple):
            a: int
            b: str

        self.assertIsInstance(Foo.insert(), Query)
        self.assertIsInstance(Foo.select(), Query)
        self.assertIsInstance(Foo.update(Foo.a == 1), Query)
        self.assertIsInstance(Foo.delete(), Query)
