# Copyright 2018 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.engines.base import Engine
from aql.engines.sql import SqlEngine
from aql.engines.sqlite import SqliteEngine


class SqliteEngineTest(TestCase):
    maxDiff = 1500

    def test_get_engine(self):
        engine = Engine.get_engine("sqlite://:memory:")
        self.assertIsInstance(engine, SqliteEngine)

    def test_inheritence(self):
        engine = SqliteEngine(":memory:")
        self.assertIsInstance(engine, SqlEngine)
