# Copyright 2020 John Reese
# Licensed under the MIT license

import re
from typing import Any, Pattern, Union

from .engines.base import Connection
from .errors import InvalidURI
from .types import Location

_uri_regex: Pattern = re.compile(r"(?P<engine>\w+)://(?P<location>.+)")


def connect(location: Union[str, Location], *args: Any, **kwargs: Any) -> Connection:
    """Connect to the specified database."""
    if isinstance(location, str):
        match = _uri_regex.match(location)
        if match:
            engine, database = match.groups()
            location = Location(engine, database=database)
        else:
            raise InvalidURI(f"Invalid database connection URI {location}")

    connector, engine_kls = Connection.get_connector(location.engine)
    return connector(engine_kls(), location, *args, **kwargs)
