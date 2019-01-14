# Copyright 2018 John Reese
# Licensed under the MIT license

from itertools import chain
from typing import Any, List, Tuple

from attr import astuple

from ..query import PreparedQuery, Query
from ..types import And, Clause, Comparison, Operator, Or, Select
from .base import Engine, T


class SqlEngine(Engine, name="sql"):
    """Generic SQL engine for generating standardized queries."""

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

    @staticmethod
    def render_comparison(comp: Comparison) -> Tuple[str, List[Any]]:
        op = comp.operator
        if op == Operator.eq:
            return f"`{comp.column.full_name}` == ?", [comp.value]
        if op == Operator.ne:
            return f"`{comp.column.full_name}` != ?", [comp.value]
        if op == Operator.gt:
            return f"`{comp.column.full_name}` > ?", [comp.value]
        if op == Operator.ge:
            return f"`{comp.column.full_name}` >= ?", [comp.value]
        if op == Operator.lt:
            return f"`{comp.column.full_name}` < ?", [comp.value]
        if op == Operator.le:
            return f"`{comp.column.full_name}` <= ?", [comp.value]
        raise NotImplementedError(f"unsupported operator {op}")

    def render_clause(self, clause: Clause) -> Tuple[str, List[Any]]:
        if isinstance(clause, Comparison):
            return self.render_comparison(clause)
        if isinstance(clause, And):
            clauses, params = zip(*(self.render_clause(c) for c in clause.clauses))
            return f"({' AND '.join(clauses)})", list(chain.from_iterable(params))
        if isinstance(clause, Or):
            clauses, params = zip(*(self.render_clause(c) for c in clause.clauses))
            return f"({' OR '.join(clauses)})", list(chain.from_iterable(params))
        raise NotImplementedError(f"unsupported clause {clause}")

    def select(self, query: Query[T]) -> PreparedQuery[T]:
        columns = ", ".join(f"`{column.full_name}`" for column in query._columns)
        selector = "DISTINCT" if query._selector == Select.distinct else "ALL"
        sql = f"SELECT {selector} {columns} FROM `{query.table._name}`"
        parameters: List[Any] = []

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
