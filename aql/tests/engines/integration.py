# Copyright 2020 John Reese
# Licensed under the MIT license

from sqlite3 import OperationalError

from aiounittest import AsyncTestCase

import aql


@aql.table
class Foo:
    id: int
    name: str


class IntegrationTest(AsyncTestCase):
    async def test_end_to_end_sqlite(self):
        async with aql.connect("sqlite://:memory:") as db:
            self.assertIsInstance(db, aql.engines.SqliteConnection)
            query = Foo.select()
            result = db.execute(query)
            self.assertIsInstance(result, aql.Result)

            with self.assertRaises(OperationalError):
                await db.execute(query)

            query = Foo.create()
            await db.execute(query)

            a = Foo(1, "hello")
            b = Foo(2, "world!")
            query = Foo.insert().values(a, b)
            await db.execute(query)

            rows = await db.execute(Foo.select())
            self.assertEqual(rows, [a, b])

            rows = await db.execute(
                Foo.select().where(Foo.name.in_(["hello", "world", "buzz"]))
            )
            self.assertEqual(rows, [a])

    async def test_end_to_end_mysql(self):
        try:
            async with aql.connect(
                aql.Location(
                    "mysql", host="localhost", port=3306, user="root", database="test"
                )
            ) as db:
                self.assertIsInstance(db, aql.engines.MysqlConnection)
                query = Foo.select()
                result = db.execute(query)
                self.assertIsInstance(result, aql.Result)

                with self.assertRaisesRegex(
                    Exception, "Table 'test.foo' doesn't exist"
                ):
                    await db.execute(query)

                query = Foo.create()
                await db.execute(query)

                a = Foo(1, "hello")
                b = Foo(2, "world!")
                query = Foo.insert().values(a, b)
                await db.execute(query)

                rows = await db.execute(Foo.select())
                self.assertEqual(rows, [a, b])

                rows = await db.execute(
                    Foo.select().where(Foo.name.in_(["hello", "world", "buzz"]))
                )
                self.assertEqual(rows, [a])

        except Exception as e:  # pylint: disable=broad-except
            if "Can't connect to MySQL server on 'localhost'" in str(e):
                self.skipTest(e)
