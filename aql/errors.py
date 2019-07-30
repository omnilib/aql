# Copyright 2019 John Reese
# Licensed under the MIT license


class AqlError(Exception):
    pass


class BuildError(AqlError):
    pass


class DuplicateColumnName(AqlError):
    pass


class QueryError(AqlError):
    pass


class UnsafeQuery(AqlError):
    pass
