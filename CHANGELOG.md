aql
===

v0.4.1
------

Bugfix release

* Include py.typed for PEP 561 support (#27)
* Tested on Python 3.9

```
$ git shortlog -s v0.4.0...v0.4.1
     5	John Reese
     1	pyup.io bot
```


v0.4.0
------

Feature release

- Add support for ORDER BY clauses in SELECT queries
- Fixes for placeholders on generated Mysql queries
- First steps towards Sphinx documentation
- Added aql to Omnilib

```
$ git shortlog -s v0.3.0...v0.4.0
     4	John Reese
```


v0.3.0
------

Feature release

- Added support for mysql connections via aiomysql
- Fixed mysql query generation to use correct placeholders for aiomysql

```
$ git shortlog -s v0.2.0...v0.3.0
    10	John Reese
```


v0.2.0
------

Feature release:

- Corrected generated SQL for Sqlite and Mysql for quoted column names
- Connection.execute() now returns an intermediate Result object that
  can be awaited
- End-to-end integration test creates table, inserts, and selects rows
- Fixed lint and typing issues

```
$ git shortlog -s v0.1.1...v0.2.0
     6	John Reese
     1	pyup-bot
     3	pyup.io bot
```


v0.1.1
------

Pre-alpha v0.1.1

```
$ git shortlog -s v0.1.0...v0.1.1
     2	John Reese
```


v0.1.0
------

Pre-alpha v0.1.0

```
$ git shortlog -s 35886a4fa6f14d3821cf5e8d0ab0428cafce5c1b...v0.1.0
     1	John Reese
```

