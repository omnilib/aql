# Copyright 2020 John Reese
# Licensed under the MIT license

from unittest import TestCase

from aql.types import PrimaryKey, Unique


class TypesTest(TestCase):
    def test_primary_key(self):
        v = object()
        pk = PrimaryKey(v)

        self.assertIs(pk.value, v)

    def test_unique(self):
        v = object()
        uk = Unique(v)

        self.assertIs(uk.value, v)
