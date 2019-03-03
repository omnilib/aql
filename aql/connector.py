# Copyright 2018 John Reese
# Licensed under the MIT license


from .engines.base import Connection, Engine


def connect(location: str) -> Connection:
    """Connect to the specified database."""
    return Engine.get_engine(location).connect()
