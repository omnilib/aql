# Copyright 2018 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.connector import connect


class ConnectorTest(TestCase):
    def test_connect_sql(self):
        with self.assertRaises(NotImplementedError):
            connect("sql://location")
