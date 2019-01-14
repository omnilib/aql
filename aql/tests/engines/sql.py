# Copyright 2018 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.engines.sql import SqlEngine
from aql.query import PreparedQuery
from aql.table import table


@table
class Contact:
    id: int
    name: str
    title: str = ""


class SqlEngineTest(TestCase):
    def test_insert(self):
        engine = SqlEngine("whatever")

        a = Contact(1, "Jack", "Janitor")
        b = Contact(2, "Jill", "Owner")
        query = Contact.insert().values(a, b)
        pquery = engine.prepare(query)

        sql = (
            "INSERT INTO `Contact` (`Contact.id`, `Contact.name`, `Contact.title`) "
            "VALUES (?,?,?), (?,?,?)"
        )
        parameters = [1, "Jack", "Janitor", 2, "Jill", "Owner"]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_select_simple(self):
        engine = SqlEngine("whatever")

        query = Contact.select().where(Contact.id > 5).limit(10)
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact.id`, `Contact.name`, `Contact.title` "
            "FROM `Contact` "
            "WHERE (`Contact.id` > ?) "
            "LIMIT ?"
        )
        parameters = [5, 10]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)
