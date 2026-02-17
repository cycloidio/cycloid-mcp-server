"""Common type definitions used across the codebase."""

from typing import Any, Dict, List, Optional, Union

# Common type aliases for better readability
JSONDict = Dict[str, Any]
JSONList = List[JSONDict]
CliFlags = Dict[str, Union[str, bool]]
StringList = List[str]
OptionalString = Optional[str]
OptionalStringList = Optional[StringList]
CliResponse = Union[JSONDict, JSONList, str]
