aql
===

Simple, async query library for modern Python

[![build status](https://github.com/omnilib/aql/workflows/Build/badge.svg)](https://github.com/omnilib/aql/actions)
[![code coverage](https://img.shields.io/codecov/c/gh/omnilib/aql)](https://codecov.io/gh/omnilib/aql)
[![version](https://img.shields.io/pypi/v/aql.svg)](https://pypi.org/project/aql)
[![license](https://img.shields.io/pypi/l/aql.svg)](https://github.com/omnilib/aql/blob/main/LICENSE)
[![code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Highlights
----------

aql is a simple, modern, and composable query builder, with support for asynchronous
execution of queries against multiple database backends using a unified API.
aql uses modern, type annotated data structures for both table definitions and queries.

*aql is still in early alpha. Not all features are available or finalized.*

Define tables:

```python
@table("objects")
class Object:
    id: PrimaryKey[AutoIncrement[int]]
    name: Unique[str]
    description: text
    created: datetime
```

Build queries:

```python
query = (
    Object.select()
    .where(Object.id >= 25)
    .order_by(Object.name)
    .limit(5)
)

sql, params = SqlEngine.prepare(query)
# "select * from `objects` where `id` >= ? order by `name` asc limit 5", (25)
```

Execute queries:

```python
async with connect(...) as db:
    cursor = db.execute(Object.select().where(Object.id < 100))
    async for row in cursor:
        print(f"{row.id} {row.name} {row.description}")
```

Simple actions:

```python
async with connect(...) as db:
    rows = await db.get(Object, Object.id == 100)
    rows[0].description += "updated"

    await db.modify(Object, rows)
```

License
-------

aql is copyright [Amethyst Reese](https://noswap.com), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
