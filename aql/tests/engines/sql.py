# Copyright 2020 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.engines.sql import SqlEngine
from aql.errors import BuildError, UnsafeQuery
from aql.query import PreparedQuery
from aql.table import table
from aql.types import And, Join, Or, TableJoin


@table
class Contact:
    contact_id: int
    name: str
    title: str = ""


@table
class Note:
    note_id: int
    contact_id: int
    content: str


class SqlEngineTest(TestCase):
    maxDiff = 1500

    def test_insert(self):
        engine = SqlEngine()

        a = Contact(1, "Jack", "Janitor")
        b = Contact(2, "Jill", "Owner")
        query = Contact.insert().values(a, b)
        pquery = engine.prepare(query)

        sql = (
            "INSERT INTO `Contact` "
            "(`contact_id`, `name`, `title`) "
            "VALUES (?,?,?), (?,?,?)"
        )
        parameters = [1, "Jack", "Janitor", 2, "Jill", "Owner"]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_render_comparison(self):
        engine = SqlEngine()

        for comp, sql, params in (
            (Contact.name == "Jack", "`Contact`.`name` = ?", ["Jack"]),
            (Contact.name != "Jack", "`Contact`.`name` != ?", ["Jack"]),
            (Contact.name == Note.content, "`Contact`.`name` = `Note`.`content`", []),
            (
                Contact.name.in_(["Jack", "Jill"]),
                "`Contact`.`name` IN (?,?)",
                ["Jack", "Jill"],
            ),
        ):
            self.assertEqual(engine.render_comparison(comp), (sql, params))

    def test_render_clause(self):
        engine = SqlEngine()

        for clause, sql, params in (
            (Contact.name == "Jack", "`Contact`.`name` = ?", ["Jack"]),
            (Contact.name != "Jack", "`Contact`.`name` != ?", ["Jack"]),
            (Contact.name == Note.content, "`Contact`.`name` = `Note`.`content`", []),
            (
                Contact.name.in_(["Jack", "Jill"]),
                "`Contact`.`name` IN (?,?)",
                ["Jack", "Jill"],
            ),
            (
                And(Contact.name != "Jack", Contact.name != "Jill"),
                "(`Contact`.`name` != ? AND `Contact`.`name` != ?)",
                ["Jack", "Jill"],
            ),
            (
                Or(Contact.name == "Jack", Contact.name == "Jill"),
                "(`Contact`.`name` = ? OR `Contact`.`name` = ?)",
                ["Jack", "Jill"],
            ),
        ):
            self.assertEqual(engine.render_clause(clause), (sql, params))

        with self.assertRaises(NotImplementedError):
            engine.render_clause(object())

    def test_render_join(self):
        engine = SqlEngine()

        for join, sql, params in (
            (TableJoin(Note, Join.inner), "INNER JOIN `Note`", []),
            (TableJoin(Note, Join.left), "LEFT JOIN `Note`", []),
            (TableJoin(Note, Join.right), "RIGHT JOIN `Note`", []),
        ):
            self.assertEqual(engine.render_join(join), (sql, params))

        with self.assertRaises(NotImplementedError):
            join = TableJoin(Note, -1)
            engine.render_join(join)

    def test_select_simple(self):
        engine = SqlEngine()

        query = Contact.select().where(Contact.contact_id > 5).limit(10)
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact`.`contact_id`, `Contact`.`name`, `Contact`.`title` "
            "FROM `Contact` "
            "WHERE (`Contact`.`contact_id` > ?) "
            "LIMIT ?"
        )
        parameters = [5, 10]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_select_where(self):
        engine = SqlEngine()

        query = Contact.select().where(
            Contact.contact_id > 5, Contact.contact_id < 100, grouping=Or
        )
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact`.`contact_id`, `Contact`.`name`, `Contact`.`title` "
            "FROM `Contact` "
            "WHERE (`Contact`.`contact_id` > ? OR `Contact`.`contact_id` < ?)"
        )
        parameters = [5, 100]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

        query = (
            Contact.select()
            .where(Contact.contact_id < 5, Contact.contact_id > 100, grouping=Or)
            .where(
                Or(
                    Contact.title.in_(["Janitor", "Owner"]),
                    Contact.title.like(r"%Engineer%"),
                    And(Contact.contact_id < 1000, Contact.contact_id > 500),
                )
            )
        )
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact`.`contact_id`, `Contact`.`name`, `Contact`.`title` "
            "FROM `Contact` "
            "WHERE (`Contact`.`contact_id` < ? OR `Contact`.`contact_id` > ?) AND "
            "((`Contact`.`title` IN (?,?) OR `Contact`.`title` LIKE ? OR "
            "(`Contact`.`contact_id` < ? AND `Contact`.`contact_id` > ?)))"
        )
        parameters = [5, 100, "Janitor", "Owner", r"%Engineer%", 1000, 500]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_select_join_using(self):
        engine = SqlEngine()

        query = (
            Contact.select(Contact.contact_id, Contact.name, Note.note_id, Note.content)
            .join(Note)
            .using(Note.contact_id)
        )
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact`.`contact_id`, `Contact`.`name`, "
            "`Note`.`note_id`, `Note`.`content` "
            "FROM `Contact` "
            "INNER JOIN `Note` "
            "USING (`contact_id`)"
        )
        parameters = []

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

        with self.assertRaises(BuildError):
            query.on(Note.contact_id == Contact.contact_id)

    def test_select_join_on(self):
        engine = SqlEngine()

        query = (
            Contact.select(Contact.contact_id, Contact.name, Note.note_id, Note.content)
            .join(Note)
            .on(Note.contact_id == Contact.contact_id)
        )
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact`.`contact_id`, `Contact`.`name`, "
            "`Note`.`note_id`, `Note`.`content` "
            "FROM `Contact` "
            "INNER JOIN `Note` "
            "ON `Note`.`contact_id` = `Contact`.`contact_id`"
        )
        parameters = []

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

        with self.assertRaises(BuildError):
            query.using(Note.contact_id)

    def test_select_join_compound(self):
        engine = SqlEngine()

        query = (
            Contact.select(Contact.contact_id, Contact.name, Note.note_id, Note.content)
            .join(Note, Join.left)
            .on(Note.contact_id == Contact.contact_id)
            .join(Note)
            .using(Note.contact_id)
            .where(Contact.contact_id > 10, Note.content != "")
            .limit(20)
            .offset(50)
        )
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact`.`contact_id`, `Contact`.`name`, "
            "`Note`.`note_id`, `Note`.`content` "
            "FROM `Contact` "
            "LEFT JOIN `Note` "
            "ON `Note`.`contact_id` = `Contact`.`contact_id` "
            "INNER JOIN `Note` "
            "USING (`contact_id`) "
            "WHERE (`Contact`.`contact_id` > ? AND `Note`.`content` != ?) "
            "LIMIT ? OFFSET ?"
        )
        parameters = [10, "", 20, 50]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_select_groupby(self):
        engine = SqlEngine()

        query = Contact.select().groupby(Contact.title)
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact`.`contact_id`, `Contact`.`name`, `Contact`.`title` "
            "FROM `Contact` "
            "GROUP BY `Contact`.`title`"
        )
        parameters = []

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_select_groupby_having(self):
        engine = SqlEngine()

        query = Contact.select().groupby(Contact.title).having(Contact.contact_id < 100)
        pquery = engine.prepare(query)

        sql = (
            "SELECT ALL `Contact`.`contact_id`, `Contact`.`name`, `Contact`.`title` "
            "FROM `Contact` "
            "GROUP BY `Contact`.`title` "
            "HAVING (`Contact`.`contact_id` < ?)"
        )
        parameters = [100]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_update(self):
        engine = SqlEngine()

        query = Contact.update(Contact.title == "Engineer", Contact.contact_id == 5)
        pquery = engine.prepare(query)

        sql = "UPDATE `Contact` SET `Contact`.`title` = ?, `Contact`.`contact_id` = ?"
        parameters = ["Engineer", 5]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_update_limit(self):
        engine = SqlEngine()

        query = Contact.update(
            Contact.title == "Engineer", Contact.contact_id == 5
        ).limit(5)
        pquery = engine.prepare(query)

        sql = (
            "UPDATE `Contact` SET `Contact`.`title` = ?, "
            "`Contact`.`contact_id` = ? LIMIT ?"
        )
        parameters = ["Engineer", 5, 5]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_update_where(self):
        engine = SqlEngine()

        query = Contact.update(
            Contact.title == "Engineer", Contact.contact_id == 5
        ).where(Contact.contact_id < 100, Contact.title == "Developer")
        pquery = engine.prepare(query)

        sql = (
            "UPDATE `Contact` "
            "SET `Contact`.`title` = ?, `Contact`.`contact_id` = ? "
            "WHERE (`Contact`.`contact_id` < ? AND `Contact`.`title` = ?)"
        )
        parameters = ["Engineer", 5, 100, "Developer"]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_delete_limit(self):
        engine = SqlEngine()

        query = Contact.delete().limit(5)
        pquery = engine.prepare(query)

        sql = "DELETE FROM `Contact` LIMIT ?"
        parameters = [5]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_delete_where(self):
        engine = SqlEngine()

        query = Contact.delete().where(Contact.contact_id < 100)
        pquery = engine.prepare(query)

        sql = "DELETE FROM `Contact` WHERE (`Contact`.`contact_id` < ?)"
        parameters = [100]

        self.assertIsInstance(pquery, PreparedQuery)
        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, parameters)

    def test_delete_unsafe(self):
        engine = SqlEngine()

        query = Contact.delete()
        with self.assertRaises(UnsafeQuery):
            engine.prepare(query)
