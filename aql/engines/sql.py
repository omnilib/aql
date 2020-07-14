# Copyright 2020 John Reese
# Licensed under the MIT license

from datetime import date, datetime
from itertools import chain
from typing import Any, List

from attr import astuple

from ..column import Column
from ..errors import UnsafeQuery
from ..query import PreparedQuery, Query
from ..types import (
    And,
    Blob,
    Clause,
    Comparison,
    Join,
    Operator,
    Or,
    Select,
    SqlParams,
    TableJoin,
    Text,
)
from .base import Engine, T, q


class SqlEngine(Engine, name="sql"):
    """Generic SQL engine for generating standardized queries."""

    PLACEHOLDER = "?"

    OPS = {
        Operator.eq: "=",
        Operator.ne: "!=",
        Operator.gt: ">",
        Operator.ge: ">=",
        Operator.lt: "<",
        Operator.le: "<=",
        Operator.in_: "IN",
        Operator.like: "LIKE",
        Operator.ilike: "ILIKE",
    }

    TYPES = {
        bool: "BOOLEAN",
        int: "BIGINT",
        float: "DOUBLE",
        str: "VARCHAR(255)",
        bytes: "VARBINARY(255)",
        Text: "TEXT",
        Blob: "BLOB",
        date: "DATE",
        datetime: "DATETIME",
    }

    def insert(self, query: Query[T]) -> PreparedQuery[T]:
        columns = ", ".join(q(column.name) for column in query._columns)
        rows = [astuple(row) for row in query._rows]
        values = ", ".join(
            f"({','.join(self.PLACEHOLDER for _ in row)})" for row in rows
        )
        parameters = list(chain.from_iterable(rows))
        sql = f"INSERT INTO {q(query.table)} ({columns}) VALUES {values}"

        return PreparedQuery(query.table, sql, parameters)

    def render_comparison(self, comp: Comparison) -> SqlParams:
        op = self.OPS[comp.operator]
        if comp.operator in (Operator.in_,):
            val = f"({','.join(self.PLACEHOLDER for _ in comp.value)})"
            params = list(comp.value)
        elif isinstance(comp.value, Column):
            val = q(comp.value)
            params = []
        else:
            val = "?"
            params = [comp.value]

        return f"{q(comp.column)} {op} {val}", params

    def render_clause(self, clause: Clause) -> SqlParams:
        if isinstance(clause, Comparison):
            return self.render_comparison(clause)
        if isinstance(clause, And):
            clauses, params = zip(*(self.render_clause(c) for c in clause.clauses))
            return f"({' AND '.join(clauses)})", list(chain.from_iterable(params))
        if isinstance(clause, Or):
            clauses, params = zip(*(self.render_clause(c) for c in clause.clauses))
            return f"({' OR '.join(clauses)})", list(chain.from_iterable(params))
        raise NotImplementedError(f"unsupported clause {clause}")

    def render_join(self, join: TableJoin) -> SqlParams:
        parameters: List[Any] = []

        if join.style == Join.inner:
            sql = f"INNER JOIN {q(join.table)}"
        elif join.style == Join.left:
            sql = f"LEFT JOIN {q(join.table)}"
        elif join.style == Join.right:
            sql = f"RIGHT JOIN {q(join.table)}"
        else:
            raise NotImplementedError(f"unsupported join type {join.style}")

        if join.on:
            clauses, params = zip(*(self.render_clause(c) for c in join.on))
            sql = f"{sql} ON {' AND '.join(clauses)}"
            parameters.extend(chain.from_iterable(params))
        elif join.using:
            columns = ", ".join(q(column.name) for column in join.using)
            sql = f"{sql} USING ({columns})"

        return sql, parameters

    def select(self, query: Query[T]) -> PreparedQuery[T]:
        columns = ", ".join(q(column) for column in query._columns)
        selector = "DISTINCT" if query._selector == Select.distinct else "ALL"
        sql = f"SELECT {selector} {columns} FROM {q(query.table)}"
        parameters: List[Any] = []

        if query._joins:
            clauses, params = zip(*(self.render_join(join) for join in query._joins))
            sql = f"{sql} {' '.join(clauses)}"
            parameters.extend(chain.from_iterable(params))

        if query._where:
            clauses, params = zip(*(self.render_clause(c) for c in query._where))
            sql = f"{sql} WHERE {' AND '.join(clauses)}"
            parameters.extend(chain.from_iterable(params))

        if query._groupby:
            columns = ", ".join(q(column) for column in query._groupby)
            sql = f"{sql} GROUP BY {columns}"

            if query._having:
                clauses, params = zip(*(self.render_clause(c) for c in query._having))
                sql = f"{sql} HAVING {' AND '.join(clauses)}"
                parameters.extend(chain.from_iterable(params))

        if query._limit:
            sql = f"{sql} LIMIT ?"
            parameters.append(query._limit)

        if query._offset:
            sql = f"{sql} OFFSET ?"
            parameters.append(query._offset)

        return PreparedQuery(query.table, sql, parameters)

    def update(self, query: Query[T]) -> PreparedQuery[T]:
        columns, params = zip(*list(query._updates.items()))
        updates = [f"{q(col)} = {self.PLACEHOLDER}" for col in columns]
        sql = f"UPDATE {q(query.table)} SET {', '.join(updates)}"
        parameters = list(params)

        if query._where:
            clauses, params = zip(*(self.render_clause(c) for c in query._where))
            sql = f"{sql} WHERE {' AND '.join(clauses)}"
            parameters.extend(chain.from_iterable(params))

        if query._limit:
            sql = f"{sql} LIMIT ?"
            parameters.append(query._limit)

        return PreparedQuery(query.table, sql, parameters)

    def delete(self, query: Query[T]) -> PreparedQuery[T]:
        sql = f"DELETE FROM {q(query.table)}"
        parameters: List[Any] = []

        if not (query._where or query._limit or query._everything):
            raise UnsafeQuery(
                "Unsafe delete query: specify where(), limit(), or everything()"
            )

        if query._where:
            clauses, params = zip(*(self.render_clause(c) for c in query._where))
            sql = f"{sql} WHERE {' AND '.join(clauses)}"
            parameters.extend(chain.from_iterable(params))

        if query._limit:
            sql = f"{sql} LIMIT ?"
            parameters.append(query._limit)

        return PreparedQuery(query.table, sql, parameters)
