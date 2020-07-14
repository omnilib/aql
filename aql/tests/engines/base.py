# Copyright 2020 John Reese
# Licensed under the MIT license

from unittest import TestCase
from unittest.mock import patch

from aql.column import Column
from aql.engines.base import Engine
from aql.query import PreparedQuery, Query
from aql.table import Table

one: Table = Table("foo", [Column("a"), Column("b")])


class MockEngine(Engine, name="mock"):
    def select(self, query):  # pylint: disable=no-self-use
        return PreparedQuery(query.table, "select", [])


class EngineTest(TestCase):
    def test_prepare(self):
        engine = MockEngine()

        query = Query(one).select()
        pquery = engine.prepare(query)

        self.assertEqual(pquery.table, one)
        self.assertEqual(pquery.sql, "select")
        self.assertEqual(pquery.parameters, [])

        with self.assertRaises(NotImplementedError):
            query = Query(one).insert().values([1, 2])
            engine.prepare(query)

    @patch("aql.engines.base.LOG")
    def test_register_duplicate(self, log_mock):
        # pylint: disable=no-self-use,unused-variable
        class FreshEngine(Engine, name="mock2"):
            pass

        log_mock.warning.assert_not_called()

        class DuplicateEngine(Engine, name="mock2"):
            pass

        log_mock.warning.assert_called_once()
