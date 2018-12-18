aql
===

asyncio query generator

[![build status](https://travis-ci.org/jreese/aql.svg?branch=master)](https://travis-ci.org/jreese/aql)
[![version](https://img.shields.io/pypi/v/aql.svg)](https://pypi.org/project/aql)
[![license](https://img.shields.io/pypi/l/aql.svg)](https://github.com/jreese/aql/blob/master/LICENSE)
[![code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


Goals
-----

aql is a modern, composable query builder, with support for async execution of 
queries against multiple database backends.  aql uses modern, type annotated
data structures for both tables and queries.

Define tables:

```python
@table
class Objects:
    id: PrimaryKey[int]
    name: Unique[str]
    description: text
    created: datetime
```

Build queries:

```python
query = (
    aql.select(Objects)
    .where(Objects.id >= 25)
    .order_by(Objects.name)
    .limit(5)
)

sql, params = query.prepare(backend=sqlite)
# "select * from `objects` where `id` >= ? order by `name` asc limit 5", (25)
```

Execute queries:

```python
async with connect(...) as db:
    result = db.select(Objects)
    async for row in result:
        print(f"{row.id} {row.name} {row.description}")
```

Modify data:

```python
async with connect(...) as db:
    result = db.select(Objects)
    rows = await result.rows()
    for row in rows:
        row.description += "updated"

    await db.update(Objects, rows)
```


License
-------

aql is copyright [John Reese](https://jreese.sh), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
