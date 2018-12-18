# Copyright 2018 John Reese
# Licensed under the MIT license

from unittest import TestCase


class ColumnTest(TestCase):
    def test_column_comparisons(self):
        from aql.column import Column, Operation
        from aql.types import Operator

        column = Column(name="foo", ctype=int)

        for op, oper in (
            (column == 25, Operator.eq),
            (column != 25, Operator.ne),
            (column >= 25, Operator.ge),
            (column <= 25, Operator.le),
            (column > 25, Operator.gt),
            (column < 25, Operator.lt),
        ):
            self.assertIsInstance(op, Operation)
            self.assertEqual(id(op.column), id(column))
            self.assertEqual(op.operator, oper)
            self.assertEqual(op.value, 25)

        op = column.like("foo%")
        self.assertIsInstance(op, Operation)
        self.assertEqual(id(op.column), id(column))
        self.assertEqual(op.operator, Operator.like)
        self.assertEqual(op.value, "foo%")

        op = column.ilike("foo%")
        self.assertIsInstance(op, Operation)
        self.assertEqual(id(op.column), id(column))
        self.assertEqual(op.operator, Operator.ilike)
        self.assertEqual(op.value, "foo%")

        values = [1, 2, 3]
        op = column.in_(values)
        self.assertIsInstance(op, Operation)
        self.assertEqual(id(op.column), id(column))
        self.assertEqual(op.operator, Operator.in_)
        self.assertEqual(op.value, values)
