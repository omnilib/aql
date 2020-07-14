# Copyright 2020 John Reese
# Licensed under the MIT license

from datetime import date
from typing import Optional
from unittest import TestCase

from aql.column import AutoIncrement, Column, Index, Primary, Unique
from aql.engines.sqlite import SqliteEngine
from aql.errors import BuildError
from aql.table import Table, table
from aql.types import Text


class SqliteEngineTest(TestCase):
    maxDiff = 1500

    def test_create(self):
        engine = SqliteEngine()

        @table(Primary("contact_id"), Unique("title", name=""))
        class Contact:
            contact_id: int
            name: str
            title: str = ""

        sql = (
            "CREATE TABLE IF NOT EXISTS `Contact` ("
            "`contact_id` BIGINT NOT NULL, "
            "`name` VARCHAR(255) NOT NULL, "
            "`title` VARCHAR(255) NOT NULL DEFAULT '', "
            "PRIMARY KEY (`contact_id`), "
            "UNIQUE (`title`))"
        )

        query = Contact.create(if_not_exists=True)
        pquery = engine.prepare(query)

        self.assertEqual(pquery.table, Contact)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, [])

        @table("members", Index("country", "postcode"))
        class Member:
            mid: Primary[AutoIncrement[int]]
            name: Unique[str]
            birthday: Optional[date]
            country: Optional[str]
            postcode: Optional[int]
            nickname: Index[Optional[str]] = ""
            bio: Text = ""

        sql = (
            "CREATE TABLE `members` ("
            "`mid` BIGINT PRIMARY KEY AUTOINCREMENT NOT NULL, "
            "`name` VARCHAR(255) UNIQUE NOT NULL, "
            "`birthday` DATE, "
            "`country` VARCHAR(255), "
            "`postcode` BIGINT, "
            "`nickname` VARCHAR(255) DEFAULT '', "
            "`bio` TEXT NOT NULL DEFAULT '')"
        )

        query = Member.create()
        pquery = engine.prepare(query)

        self.assertEqual(pquery.table, Member)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, [])

    def test_create_manual(self):
        engine = SqliteEngine()

        Foo = Table(
            "foo",
            [Column("a", Primary[AutoIncrement[int]]), Column("b", str), Index("b")],
        )

        sql = (
            "CREATE TABLE `foo` ("
            "`a` BIGINT PRIMARY KEY AUTOINCREMENT NOT NULL, "
            "`b` VARCHAR(255) NOT NULL)"
        )

        query = Foo.create()
        pquery = engine.prepare(query)

        self.assertEqual(pquery.table, Foo)
        self.assertEqual(pquery.sql, sql)
        self.assertEqual(pquery.parameters, [])

    def test_create_no_type(self):
        engine = SqliteEngine()

        Foo = Table(
            "foo", [Column("a", Primary[AutoIncrement[int]]), Column("b"), Index("b")]
        )

        with self.assertRaises(BuildError):
            engine.prepare(Foo.create())

    def test_create_bad_type(self):
        engine = SqliteEngine()

        Foo = Table(
            "foo",
            [Column("a", Primary[AutoIncrement[int]]), Column("b", list), Index("b")],
        )

        with self.assertRaises(BuildError):
            engine.prepare(Foo.create())
