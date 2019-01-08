# Copyright 2018 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.column import Column
from aql.errors import BuildError
from aql.query import Query
from aql.table import Table
from aql.types import QueryAction, Selector


class QueryTest(TestCase):
    def test_select(self):
        one = Table("foo", [Column("a"), Column("b")])
        two = Table("bar", [Column("e"), Column("f")])

        query = (
            Query(one)
            .select(one.a)
            .join(two, one.a == two.e)
            .where(one.b > 5, two.f < 10)
            .limit(7)
        )

        self.assertEqual(query._action, QueryAction.select)
        self.assertEqual(query._selector, Selector.all)
        self.assertEqual(query._columns, [one.a])
        self.assertEqual(query._joins, [(two, (one.a == two.e,))])
        self.assertEqual(len(query._where), 1)
        self.assertEqual(query._where[0].clauses, (one.b > 5, two.f < 10))
        self.assertEqual(query._limit, 7)
        self.assertEqual(query._offset, None)

        query.offset(25)
        self.assertEqual(query._offset, 25)

        query.distinct()
        self.assertEqual(query._selector, Selector.distinct)

    def test_decorator_start(self):
        tbl = Table("foo", [])

        with self.assertRaises(BuildError):
            query = Query(tbl).insert().select()

        with self.assertRaises(BuildError):
            query = Query(tbl).insert().values().select().where()

    def test_decorator_only(self):
        tbl = Table("foo", [])

        with self.assertRaises(BuildError):
            query = Query(tbl).insert().where()
