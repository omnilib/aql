# Copyright 2019 John Reese
# Licensed under the MIT license

import re
from typing import Any, Pattern

from .engines.base import Connection
from .errors import InvalidURI

_uri_regex: Pattern = re.compile(r"(?P<engine>\w+)://(?P<location>.+)")


def connect(uri: str, *args: Any, **kwargs: Any) -> Connection:
    """Connect to the specified database."""
    match = _uri_regex.match(uri)
    if match:
        scheme, path = match.groups()
        connector, engine_kls = Connection.get_connector(scheme)
        return connector(engine_kls(), path, *args, **kwargs)
    raise InvalidURI(f"Invalid database connection URI {uri}")
