# Copyright 2018 John Reese
# Licensed under the MIT license

from itertools import chain
from typing import Any, List

from attr import astuple

from ..column import Column
from ..query import PreparedQuery, Query
from ..types import (
    And,
    Clause,
    Comparison,
    Join,
    Operator,
    Or,
    Select,
    SqlParams,
    TableJoin,
)
from .base import Engine, T


class SqlEngine(Engine, name="sql"):
    """Generic SQL engine for generating standardized queries."""

    OPS = {
        Operator.eq: "==",
        Operator.ne: "!=",
        Operator.gt: ">",
        Operator.ge: ">=",
        Operator.lt: "<",
        Operator.le: "<=",
        Operator.in_: "IN",
        Operator.like: "LIKE",
        Operator.ilike: "ILIKE",
    }

    def __init__(self, location: str, placeholder: str = "?"):
        super().__init__(location)
        self.placeholder = placeholder

    def insert(self, query: Query[T]) -> PreparedQuery[T]:
        columns = ", ".join(f"`{column.full_name}`" for column in query._columns)
        rows = [astuple(row) for row in query._rows]
        values = ", ".join(
            f"({','.join(self.placeholder for _ in row)})" for row in rows
        )
        parameters = list(chain.from_iterable(rows))
        sql = f"INSERT INTO `{query.table._name}` ({columns}) VALUES {values}"

        return PreparedQuery(query.table, sql, parameters)

    def render_comparison(self, comp: Comparison) -> SqlParams:
        col = comp.column.full_name
        op = self.OPS[comp.operator]
        if comp.operator in (Operator.in_,):
            val = ",".join(self.placeholder for _ in comp.value)
            params = list(comp.value)
        elif isinstance(comp.value, Column):
            val = f"`{comp.value.full_name}`"
            params = []
        else:
            val = "?"
            params = [comp.value]

        return f"`{col}` {op} {val}", params

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
            sql = f"INNER JOIN `{join.table._name}`"
        elif join.style == Join.left:
            sql = f"LEFT JOIN `{join.table._name}`"
        elif join.style == Join.right:
            sql = f"RIGHT JOIN `{join.table._name}`"

        if join.on:
            clauses, params = zip(*(self.render_clause(c) for c in join.on))
            sql = f"{sql} ON {' AND '.join(clauses)}"
            parameters.extend(chain.from_iterable(params))
        elif join.using:
            columns = ", ".join(f"`{column.name}`" for column in join.using)
            sql = f"{sql} USING ({columns})"

        return sql, parameters

    def select(self, query: Query[T]) -> PreparedQuery[T]:
        columns = ", ".join(f"`{column.full_name}`" for column in query._columns)
        selector = "DISTINCT" if query._selector == Select.distinct else "ALL"
        sql = f"SELECT {selector} {columns} FROM `{query.table._name}`"
        parameters: List[Any] = []

        if query._joins:
            clauses, params = zip(*(self.render_join(join) for join in query._joins))
            sql = f"{sql} {' '.join(clauses)}"
            parameters.extend(chain.from_iterable(params))

        if query._where:
            clauses, params = zip(*(self.render_clause(c) for c in query._where))
            sql = f"{sql} WHERE {' AND '.join(clauses)}"
            parameters.extend(chain.from_iterable(params))

        if query._limit:
            sql = f"{sql} LIMIT ?"
            parameters.append(query._limit)

        if query._offset:
            sql = f"{sql} OFFSET ?"
            parameters.append(query._offset)

        return PreparedQuery(query.table, sql, parameters)
