"""Template loading utilities for external template files."""

from functools import lru_cache
from pathlib import Path
from typing import Any

# Template directory path
TEMPLATE_DIR = Path(__file__).parent / "templates"


@lru_cache(maxsize=16)
def load_template(template_name: str) -> str:
    """
    Load a template from the templates directory with caching.

    NOTE: This cache is safe because templates are static files that don't change
    during runtime. This is NOT suitable for dynamic API data.

    Args:
        template_name: Name of the template file (with extension)

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    return template_path.read_text(encoding="utf-8")


def format_template(template_name: str, **kwargs: Any) -> str:
    """
    Load and format a template with provided variables.

    Args:
        template_name: Name of the template file
        **kwargs: Variables to substitute in the template

    Returns:
        Formatted template string
    """
    template_content = load_template(template_name)
    return template_content.format(**kwargs)


def get_stack_creation_guidance(ref: str, use_cases: str) -> str:
    """Get formatted stack creation guidance template."""
    return format_template("stack_creation_guidance.md", ref=ref, use_cases=use_cases)


def get_elicitation_fallback(
    name: str, description: str, version: str, use_cases: str, canonicals: str, ref: str
) -> str:
    """Get formatted elicitation fallback template."""
    return format_template(
        "elicitation_fallback.md",
        name=name,
        description=description,
        version=version,
        use_cases=use_cases,
        canonicals=canonicals,
        ref=ref,
    )
