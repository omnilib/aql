# Copyright 2019 John Reese
# Licensed under the MIT license

from unittest import TestCase


class SmokeTest(TestCase):
    def test_import(self):
        import aql

        self.assertTrue(aql.Column)
