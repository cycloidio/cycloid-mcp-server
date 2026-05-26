"""Event tools and resources for Cycloid MCP server."""

import asyncio
import json
import os
from typing import Any, Dict, List, Set

from fastmcp.dependencies import Depends  # type: ignore[reportAttributeAccessIssue]
from fastmcp.exceptions import ToolError
from fastmcp.resources import resource
from fastmcp.tools import tool
from fastmcp.utilities.logging import get_logger

from src.cli import CLIMixin
from src.dependencies import get_cli
from src.display_hints import build_display_hints
from src.exceptions import CycloidCLIError
from src.types import JSONDict, JSONList, OptionalString, OptionalStringList

logger = get_logger(__name__)

_DEFAULT_MAX_COMPONENTS = 50


def _get_max_components() -> int:
    try:
        return int(os.environ.get("CYCLOID_PROJECT_EVENTS_MAX_COMPONENTS", _DEFAULT_MAX_COMPONENTS))
    except (TypeError, ValueError):
        return _DEFAULT_MAX_COMPONENTS


def _extract_tag(event: JSONDict, key: str) -> str:
    """Extract the value of a tag by key from an event's tags list."""
    for tag in event.get("tags", []):
        if tag.get("key") == key:
            return str(tag.get("value", ""))
    return ""


def _event_belongs_to_project(event: JSONDict, project: str) -> bool:
    """Check whether an event is scoped to the given project.

    The Cycloid events API uses two different project tag keys depending on
    the event family:
      - "Cycloid"-type events (ci_build, configure, pause/unpause, …) only
        carry ``project_canonical``.
      - Older "Custom" events emitted by CI/CD pipelines historically also
        carried ``project`` alongside ``project_canonical``.
    Match either so both families are covered.
    """
    return (
        _extract_tag(event, "project_canonical") == project
        or _extract_tag(event, "project") == project
    )


def _extract_actors(events: JSONList) -> List[JSONDict]:
    """Extract deduplicated actor list from events.

    Different event families surface the actor differently:
      - Cycloid-type events (most platform activity) carry ``member_id`` —
        the numeric member id needed for the ``/organizations/<org>/members/
        <id>`` URL, no lookup required.
      - Custom-type events historically carry ``user`` — a username only, so
        the LLM needs to cross-reference ``CYCLOID_MEMBER_LIST`` to build a
        URL.
    Each actor dict surfaces whichever identifier(s) the source event
    provided. Deduplication keys on the available identifier so we never
    drop one or the other.
    """
    seen: Set[str] = set()
    actors: List[JSONDict] = []
    for event in events:
        member_id = _extract_tag(event, "member_id")
        username = _extract_tag(event, "user")
        if not member_id and not username:
            continue
        key = f"id:{member_id}" if member_id else f"user:{username}"
        if key in seen:
            continue
        seen.add(key)
        actor: JSONDict = {}
        if member_id:
            actor["id"] = member_id
        if username:
            actor["username"] = username
        actors.append(actor)
    return actors


async def _list_events(
    cli: CLIMixin,
    begin: OptionalString = None,
    end: OptionalString = None,
    severity: OptionalStringList = None,
    type: OptionalStringList = None,
) -> JSONList:
    """List events using `cy event list` with optional filters."""
    args: List[str] = ["list"]

    flags: JSONDict = {}
    if begin:
        flags["begin"] = begin
    if end:
        flags["end"] = end
    if severity:
        flags["severity"] = ",".join(severity)
    if type:
        flags["type"] = ",".join(type)

    events_data = await cli.execute_cli("event", args, flags=flags)
    return cli.process_cli_response(events_data, list_key=None)


async def _list_project_envs(cli: CLIMixin, project: str) -> JSONList:
    """List environments for a project."""
    envs_data = await cli.execute_cli("project", ["list-env"], flags={"project": project})
    return cli.process_cli_response(envs_data, list_key=None)


async def _list_components_for_env(cli: CLIMixin, project: str, env: str) -> JSONList:
    """List components in a project environment."""
    components_data = await cli.execute_cli(
        "components", ["list"], flags={"project": project, "env": env}
    )
    return cli.process_cli_response(components_data, list_key=None)


@tool(
    name="CYCLOID_EVENT_LIST",
    description=(
        "List organization events with optional filters (begin, end, severity, type). "
        "Returns full event payload including tags. Actor identity is in tags as "
        "{key: 'user', value: '<username>'}. "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: title (Title), "
        "severity (Severity), type (Type), timestamp (Timestamp), tags (Tags). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_events(
    begin: OptionalString = None,
    end: OptionalString = None,
    severity: OptionalStringList = None,
    type: OptionalStringList = None,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List events from Cycloid.

    Args:
        begin: Unix timestamp (string) start date.
        end: Unix timestamp (string) end date.
        severity: List of severities to include.
        type: List of event types to include.
    """
    try:
        events = await _list_events(cli, begin=begin, end=end, severity=severity, type=type)
        return {
            "events": events,
            "count": len(events),
            "_display_hints": build_display_hints(
                key_fields=["title", "severity", "type", "timestamp", "tags"],
                display_format="table",
                columns={
                    "title": "Title",
                    "severity": "Severity",
                    "type": "Type",
                    "timestamp": "Timestamp",
                    "tags": "Tags",
                },
                sort_by="timestamp",
            ),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to list events: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing events: {str(e)}")


@tool(
    name="CYCLOID_PROJECT_EVENTS",
    description=(
        "List events scoped to a specific project's components. "
        "Walks project → envs → components, then filters org-wide events by project tag. "
        "Returns events, count, and a deduplicated actors list extracted from tags[key=user]. "
        "Actor usernames can be cross-referenced with CYCLOID_MEMBER_LIST to get numeric ids "
        "for building member URLs. "
        "Hard cap: aborts with a structured error if total components exceed the configured "
        "maximum (default 50). Use begin/end/severity/type to narrow results. "
        "DISPLAY GUIDANCE: Present events as a markdown table grouped by actor. "
        "Key fields: title (Title), severity (Severity), timestamp (Timestamp), actor (Actor)."
    ),
    annotations={"readOnlyHint": True},
)
async def list_project_events(
    project: str,
    begin: OptionalString = None,
    end: OptionalString = None,
    severity: OptionalStringList = None,
    type: OptionalStringList = None,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List events scoped to a project's components.

    Args:
        project: The project canonical (required).
        begin: Unix timestamp (string) start date.
        end: Unix timestamp (string) end date.
        severity: List of severities to include.
        type: List of event types to include.
    """
    if not project:
        raise ToolError("Project canonical is required")

    max_components = _get_max_components()

    try:
        # Fetch envs for the project
        envs = await _list_project_envs(cli, project)
        if not envs:
            return {
                "events": [],
                "count": 0,
                "actors": [],
                "project": project,
                "_display_hints": build_display_hints(
                    key_fields=["title", "severity", "timestamp", "tags"],
                    display_format="table",
                    columns={
                        "title": "Title",
                        "severity": "Severity",
                        "timestamp": "Timestamp",
                        "tags": "Tags",
                    },
                    sort_by="timestamp",
                ),
            }

        env_canonicals: List[str] = [
            e.get("canonical", "") for e in envs if e.get("canonical")
        ]

        # Fetch components for all envs in parallel (memoized per request via gather)
        component_tasks = [
            _list_components_for_env(cli, project, env) for env in env_canonicals
        ]
        components_per_env: List[JSONList] = await asyncio.gather(*component_tasks)

        # Collect unique component canonicals across all envs
        component_canonicals: Set[str] = set()
        for env_components in components_per_env:
            for comp in env_components:
                canonical = comp.get("canonical", "")
                if canonical:
                    component_canonicals.add(canonical)

        total_components = len(component_canonicals)
        if total_components > max_components:
            return {
                "error": (
                    f"Project '{project}' has {total_components} components, which exceeds "
                    f"the maximum of {max_components}. Please narrow the query to a specific "
                    f"environment using CYCLOID_COMPONENT_LIST and CYCLOID_EVENT_LIST directly, "
                    f"or set CYCLOID_PROJECT_EVENTS_MAX_COMPONENTS to raise the cap."
                ),
                "total_components": total_components,
                "max_components": max_components,
                "project": project,
            }

        # Fetch all org events once, then filter by project tag
        all_events = await _list_events(cli, begin=begin, end=end, severity=severity, type=type)

        project_events = [
            event for event in all_events
            if _event_belongs_to_project(event, project)
        ]

        actors = _extract_actors(project_events)

        return {
            "events": project_events,
            "count": len(project_events),
            "actors": actors,
            "project": project,
            "_display_hints": build_display_hints(
                key_fields=["title", "severity", "timestamp", "tags"],
                display_format="table",
                columns={
                    "title": "Title",
                    "severity": "Severity",
                    "timestamp": "Timestamp",
                    "tags": "Tags",
                },
                sort_by="timestamp",
            ),
        }

    except CycloidCLIError as e:
        raise ToolError(f"Failed to list project events: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing project events: {str(e)}")


@resource("cycloid://events")
async def get_events_resource(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> str:
    """Get all events as a resource."""
    try:
        events = await _list_events(cli)
        result = {
            "events": events,
            "count": len(events),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error("Failed to fetch events resource", extra={"error": str(e)})
        return json.dumps({"error": str(e), "events": [], "count": 0}, indent=2)
