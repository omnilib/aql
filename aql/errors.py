# Copyright 2018 John Reese
# Licensed under the MIT license


class AqlError(Exception):
    pass


class QueryError(AqlError):
    pass
