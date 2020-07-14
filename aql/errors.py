# Copyright 2020 John Reese
# Licensed under the MIT license


class AqlError(Exception):
    pass


class UnknownConnector(AqlError):
    pass


class InvalidColumnType(AqlError):
    pass


class InvalidURI(AqlError):
    pass


class BuildError(AqlError):
    pass


class DuplicateColumnName(AqlError):
    pass


class QueryError(AqlError):
    pass


class UnsafeQuery(AqlError):
    pass


class NoConnection(AqlError):
    pass
