# Copyright 2018 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.engines.base import Engine
from aql.engines.sqlite import SqliteEngine


class EngineTest(TestCase):
    def test_get_engine(self):
        engine = Engine.get_engine("sqlite://whatever")
        self.assertIsInstance(engine, Engine)
        self.assertIsInstance(engine, SqliteEngine)
        self.assertEqual(engine.location, "whatever")
