# Copyright 2019 John Reese
# Licensed under the MIT license

from typing import Optional
from unittest import TestCase

from aql.column import AutoIncrement, Column, Index, Primary, Unique
from aql.types import Comparison, Operator


class ColumnTest(TestCase):
    def test_constraints(self):
        t = AutoIncrement[int]
        self.assertEqual(t.__args__, (int,))

        t = Index[Optional[str]]
        self.assertEqual(t.__args__, (Optional[str],))

        a = Column(name="a", ctype=Primary[AutoIncrement[int]])
        self.assertEqual(a.ctype, Primary[AutoIncrement[int]])
        self.assertEqual(a.ctype.__args__, (AutoIncrement[int],))
        self.assertEqual(a.ctype.__args__[0].__args__, (int,))

        i = Index("a", "b")
        self.assertEqual(i._columns, ["a", "b"])
        self.assertEqual(i._name, "idx_a_b")

        i = Unique("c", "d")
        self.assertEqual(i._columns, ["c", "d"])
        self.assertEqual(i._name, "unq_c_d")

        i = Primary("e", "f")
        self.assertEqual(i._columns, ["e", "f"])
        self.assertEqual(i._name, "pri_e_f")

        i = Index("g", name="foobar")
        self.assertEqual(i._columns, ["g"])
        self.assertEqual(i._name, "foobar")

        self.assertEqual(Index("a", "b"), Index("a", "b"))
        self.assertNotEqual(Index("a", "b"), Index("a", "c"))
        self.assertNotEqual(Index("a", "b"), Unique("a", "b"))

    def test_column_comparisons(self):

        column = Column(name="foo", ctype=int)
        self.assertEqual(column.name, "foo")
        self.assertEqual(column.table_name, "")

        column = Column(name="foo", ctype=int, table_name="bar")
        self.assertEqual(column.name, "foo")
        self.assertEqual(column.table_name, "bar")

        for op, oper in (
            (column == 25, Operator.eq),
            (column != 25, Operator.ne),
            (column >= 25, Operator.ge),
            (column <= 25, Operator.le),
            (column > 25, Operator.gt),
            (column < 25, Operator.lt),
        ):
            self.assertIsInstance(op, Comparison)
            self.assertIs(op.column, column)
            self.assertEqual(op.operator, oper)
            self.assertEqual(op.value, 25)

        op = column.like("foo%")
        self.assertIsInstance(op, Comparison)
        self.assertIs(op.column, column)
        self.assertEqual(op.operator, Operator.like)
        self.assertEqual(op.value, "foo%")

        op = column.ilike("foo%")
        self.assertIsInstance(op, Comparison)
        self.assertIs(op.column, column)
        self.assertEqual(op.operator, Operator.ilike)
        self.assertEqual(op.value, "foo%")

        values = [1, 2, 3]
        op = column.in_(values)
        self.assertIsInstance(op, Comparison)
        self.assertIs(op.column, column)
        self.assertEqual(op.operator, Operator.in_)
        self.assertEqual(op.value, values)
