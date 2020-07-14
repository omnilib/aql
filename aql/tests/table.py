# Copyright 2020 John Reese
# Licensed under the MIT license

from typing import NamedTuple
from unittest import TestCase

from aql.column import (
    NO_DEFAULT,
    AutoIncrement,
    Column,
    ColumnType,
    Index,
    Primary,
    Unique,
)
from aql.errors import AqlError, DuplicateColumnName
from aql.query import Query
from aql.table import Table, table
from aql.types import Comparison, Operator, QueryAction


class TableTest(TestCase):
    def test_table_init(self):
        columns = [Column("a"), Column("b"), Column("foo"), Column("bar")]

        tbl = Table("test", columns)
        self.assertEqual(tbl._name, "test")
        self.assertIn("a", tbl._column_names)
        for col, tcol in zip(columns, tbl._columns):
            self.assertIs(col, tcol)
            self.assertIs(col, getattr(tbl, col.name))
        self.assertEqual(tbl._indexes, [])

        self.assertEqual(tbl.foo == 5, Comparison(columns[2], Operator.eq, 5))
        self.assertTrue("a" in tbl)
        self.assertFalse("z" in tbl)
        self.assertEqual(tbl["a"], columns[0])

        with self.assertRaises(KeyError):
            tbl["z"]

        with self.assertRaises(DuplicateColumnName):
            Table("test", columns + columns[:1])

        tbl = Table("test", columns + [Index("a")])
        self.assertEqual(tbl._indexes, [Index("a")])

        with self.assertRaises(ValueError):
            Table("test", [Column("a"), 23])

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
            b: str = ""

        self.assertIsInstance(Foo, Table)
        self.assertIsInstance(Foo.a, Column)
        self.assertIsInstance(Foo.b, Column)
        self.assertEqual(Foo._name, "foo")
        self.assertEqual(Foo._columns, [Foo.a, Foo.b])
        self.assertEqual(Foo._indexes, [])
        self.assertEqual(
            Foo._column_types, {Foo.a: ColumnType(int), Foo.b: ColumnType(str)}
        )
        self.assertEqual(Foo.a.default, NO_DEFAULT)
        self.assertEqual(Foo.b.default, "")

        foo = Foo(a=1, b="bar")
        self.assertIsInstance(foo, Foo._source)
        self.assertEqual(foo.a, 1)
        self.assertEqual(foo.b, "bar")

        @table
        class Foo:
            a: int
            b: str

        self.assertIsInstance(Foo, Table)
        self.assertEqual(Foo._name, "Foo")
        self.assertEqual(Foo._columns, [Foo.a, Foo.b])
        self.assertEqual(Foo._indexes, [])

    def test_table_decorator_indexes(self):
        @table("foo")
        class Foo:
            a: Primary[AutoIncrement[int]]
            b: Unique[str]

        self.assertIsInstance(Foo, Table)
        self.assertIsInstance(Foo.a, Column)
        self.assertIsInstance(Foo.b, Column)
        self.assertEqual(Foo._name, "foo")
        self.assertEqual(Foo._columns, [Foo.a, Foo.b])
        self.assertEqual(Foo._indexes, [])
        self.assertEqual(
            Foo._column_types,
            {
                Foo.a: ColumnType(int, autoincrement=True, constraint=Primary),
                Foo.b: ColumnType(str, constraint=Unique),
            },
        )

        @table(Primary("a"), Index("a", "b"))
        class Bar:
            a: int
            b: Index[str]

        self.assertIsInstance(Bar, Table)
        self.assertIsInstance(Bar.a, Column)
        self.assertIsInstance(Bar.b, Column)
        self.assertEqual(Bar._name, "Bar")
        self.assertEqual(Bar._columns, [Bar.a, Bar.b])
        self.assertEqual(Bar._indexes, [Primary("a"), Index("a", "b"), Index("b")])
        self.assertEqual(
            Bar._column_types,
            {Bar.a: ColumnType(int), Bar.b: ColumnType(str, constraint=Index)},
        )

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
        class Foo:
            a: int
            b: str

        query = Foo.create()
        self.assertIsInstance(query, Query)
        self.assertEqual(query._action, QueryAction.create)

        query = Foo.insert()
        self.assertIsInstance(query, Query)
        self.assertEqual(query._action, QueryAction.insert)

        query = Foo.select()
        self.assertIsInstance(query, Query)
        self.assertEqual(query._action, QueryAction.select)

        query = Foo.update(Foo.a == 1)
        self.assertIsInstance(query, Query)
        self.assertEqual(query._action, QueryAction.update)

        query = Foo.delete()
        self.assertIsInstance(query, Query)
        self.assertEqual(query._action, QueryAction.delete)
