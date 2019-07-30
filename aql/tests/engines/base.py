# Copyright 2019 John Reese
# Licensed under the MIT license

from unittest import TestCase
from unittest.mock import patch

from aql.column import Column
from aql.engines.base import Engine
from aql.engines.sql import SqlEngine
from aql.query import PreparedQuery, Query
from aql.table import Table

one: Table = Table("foo", [Column("a"), Column("b")])


class MockEngine(Engine, name="mock"):
    def select(self, query):  # pylint: disable=no-self-use
        return PreparedQuery(query.table, "select", [])


class EngineTest(TestCase):
    def test_get_engine(self):
        engine = Engine.get_engine("sql://whatever")
        self.assertIsInstance(engine, Engine)
        self.assertIsInstance(engine, SqlEngine)
        self.assertEqual(engine.location, "whatever")

        # malformed engine uri
        with self.assertRaises(ValueError):
            engine = Engine.get_engine("nothing")

        # engine not found
        with self.assertRaises(ValueError):
            engine = Engine.get_engine("fake://nothing")

    def test_prepare(self):
        engine = MockEngine("location")

        query = Query(one).select()
        pquery = engine.prepare(query)

        self.assertEqual(pquery.table, one)
        self.assertEqual(pquery.sql, "select")
        self.assertEqual(pquery.parameters, [])

        with self.assertRaises(NotImplementedError):
            query = Query(one).insert().values([1, 2])
            engine.prepare(query)

    def test_connect(self):
        engine = MockEngine("location")
        with self.assertRaises(NotImplementedError):
            engine.connect()

    @patch("aql.engines.base.LOG")
    def test_register_duplicate(self, log_mock):
        # pylint: disable=no-self-use,unused-variable
        class FreshEngine(Engine, name="mock2"):
            pass

        log_mock.warning.assert_not_called()

        class DuplicateEngine(Engine, name="mock2"):
            pass

        log_mock.warning.assert_called_once()
