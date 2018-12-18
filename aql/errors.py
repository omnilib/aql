# Copyright 2018 John Reese
# Licensed under the MIT license


class AqlError(Exception):
    pass


class DuplicateColumnName(AqlError):
    pass


class QueryError(AqlError):
    pass
