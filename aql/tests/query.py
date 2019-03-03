# Copyright 2018 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.column import Column
from aql.errors import BuildError
from aql.query import Query
from aql.table import Table
from aql.types import Join, QueryAction, Select, TableJoin

one: Table = Table("foo", [Column("a"), Column("b")])
two: Table = Table("bar", [Column("e"), Column("f")])
tre: Table = Table("bang", [Column("e"), Column("f")])


class QueryTest(TestCase):
    def test_insert(self):
        query = Query(one).insert().values((1, 2), (3, 4))

        self.assertEqual(query.table, one)
        self.assertEqual(query._action, QueryAction.insert)
        self.assertEqual(query._columns, one._columns)
        self.assertEqual(query._rows, [(1, 2), (3, 4)])

        query = Query(one).insert(one.b).values((1,), (3,)).values((2,), (4,))

        self.assertEqual(query.table, one)
        self.assertEqual(query._action, QueryAction.insert)
        self.assertEqual(query._columns, [one.b])
        self.assertEqual(query._rows, [(1,), (3,), (2,), (4,)])

    def test_select(self):
        query = Query(one).select(one.a).where(one.b > 5, two.f < 10).limit(7)

        self.assertEqual(query.table, one)
        self.assertEqual(query._action, QueryAction.select)
        self.assertEqual(query._selector, Select.all)
        self.assertEqual(query._columns, [one.a])
        self.assertEqual(len(query._where), 1)
        self.assertEqual(query._where[0].clauses, (one.b > 5, two.f < 10))
        self.assertEqual(query._limit, 7)
        self.assertEqual(query._offset, None)

        query.offset(25)
        self.assertEqual(query._offset, 25)

        query.distinct()
        self.assertEqual(query._selector, Select.distinct)

    def test_select_joins(self):
        query = Query(one).select().join(two, Join.left).on(one.a == two.e)

        self.assertEqual(query.table, one)
        self.assertEqual(query._columns, one._columns)
        self.assertEqual(
            query._joins, [TableJoin(two, Join.left, [one.a == two.e], [])]
        )

        with self.assertRaises(BuildError):
            query.using(two.f)

        query = query.join(tre).using(tre.e, tre.f)

        self.assertEqual(
            query._joins,
            [
                TableJoin(two, Join.left, [one.a == two.e], []),
                TableJoin(tre, Join.inner, [], [tre.e, tre.f]),
            ],
        )

        with self.assertRaises(BuildError):
            query.on(one.a == two.f)

    def test_select_group_by(self):
        query = Query(one).select().groupby(one.a)

        self.assertEqual(query.table, one)
        self.assertEqual(query._columns, one._columns)
        self.assertEqual(query._groupby, [one.a])
        self.assertEqual(query._having, [])

        with self.assertRaises(BuildError):
            query.groupby(one.b)

        with self.assertRaises(BuildError):
            query.having()

        query.having(one.b == 3)

        self.assertEqual(len(query._having), 1)
        self.assertEqual(query._having[0].clauses, (one.b == 3,))

    def test_update(self):
        query = (
            Query(one).update(one.a == 5, b="hello").where(one.b != "hello").limit(5)
        )

        self.assertEqual(query.table, one)
        self.assertEqual(query._action, QueryAction.update)
        self.assertEqual(query._updates, {one.a: 5, one.b: "hello"})
        self.assertEqual(len(query._where), 1)
        self.assertEqual(query._where[0].clauses, (one.b != "hello",))
        self.assertEqual(query._limit, 5)

    def test_delete(self):
        query = Query(one).delete().where(one.a == 20).limit(1)

        self.assertEqual(query.table, one)
        self.assertEqual(query._action, QueryAction.delete)
        self.assertEqual(len(query._where), 1)
        self.assertEqual(query._where[0].clauses, (one.a == 20,))
        self.assertEqual(query._limit, 1)

    def test_decorator_start(self):
        tbl = Table("foo", [])

        with self.assertRaises(BuildError):
            Query(tbl).insert().select()

        with self.assertRaises(BuildError):
            Query(tbl).insert().values().select().where()

    def test_decorator_only(self):
        tbl = Table("foo", [])

        with self.assertRaises(BuildError):
            Query(tbl).limit(5)

        with self.assertRaises(BuildError):
            Query(tbl).insert().where()