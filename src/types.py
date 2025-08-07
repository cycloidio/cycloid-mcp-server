"""Common type definitions used across the codebase."""

from typing import Any, Dict, List, Optional, Tuple, Union

# Common type aliases for better readability
JSONDict = Dict[str, Any]
JSONList = List[JSONDict]
CliFlags = Dict[str, Union[str, bool]]
StringList = List[str]
OptionalString = Optional[str]
OptionalStringList = Optional[StringList]

# More specific types to replace Any usage
CliResponse = Union[JSONDict, JSONList, str]
ElicitationResult = Tuple[bool, str, Dict[str, str]]
StackCreationParams = Dict[str, str]
