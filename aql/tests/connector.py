# Copyright 2020 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.connector import connect
from aql.engines.sql import SqlEngine
from aql.engines.sqlite import SqliteConnection
from aql.errors import InvalidURI, UnknownConnector


class ConnectorTest(TestCase):
    def test_connect_unknown(self):
        with self.assertRaises(UnknownConnector):
            connect("unknown://foo")

    def test_connect_bad_uri(self):
        with self.assertRaises(InvalidURI):
            connect("foobar")

    def test_connect_sqlite(self):
        db = connect("sqlite://foo")
        self.assertIsInstance(db, SqliteConnection)
        self.assertIsInstance(db.engine, SqlEngine)
