"""Utility for building display hints dicts for tool responses."""

from typing import Any, Dict, List, Optional


def build_display_hints(
    key_fields: List[str],
    display_format: str,
    columns: Dict[str, str],
    sort_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a display hints dict for tool responses.

    Args:
        key_fields: Ordered list of most important fields to show.
        display_format: Suggested format ("table" or "list").
        columns: Field to human-readable column header mapping.
        sort_by: Suggested default sort field.
    """
    hints: Dict[str, Any] = {
        "key_fields": key_fields,
        "display_format": display_format,
        "columns": columns,
    }
    if sort_by:
        hints["sort_by"] = sort_by
    return hints
