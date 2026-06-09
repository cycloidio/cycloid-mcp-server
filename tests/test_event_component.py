"""Tests for Event component using FastMCP Client pattern."""

import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.events import get_events_resource, list_events, list_project_events

SAMPLE_EVENT = {
    "id": 1,
    "timestamp": 1234567890000,
    "severity": "info",
    "type": "Cycloid",
    "title": "A build has been created",
    "message": "Cyclobot created the build cleanup-deployment#42",
    "tags": [
        {"key": "action", "value": "create"},
        {"key": "entity", "value": "ci_build"},
        {"key": "project", "value": "awesome-project"},
        {"key": "user", "value": "alice"},
    ],
    "icon": "fa-info-circle",
}

SAMPLE_EVENT_OTHER_PROJECT = {
    "id": 2,
    "timestamp": 1234567891000,
    "severity": "warn",
    "type": "AWS",
    "title": "Another event",
    "message": "Something happened",
    "tags": [
        {"key": "project", "value": "other-project"},
        {"key": "user", "value": "bob"},
    ],
}

SAMPLE_EVENT_NO_PROJECT_TAG = {
    "id": 3,
    "timestamp": 1234567892000,
    "severity": "info",
    "type": "Monitoring",
    "title": "Monitoring alert",
    "message": "CPU high",
    "tags": [{"key": "env", "value": "prod"}],
}

# Events spanning several action/entity tag combinations, for filter tests.
FILTER_EVENTS = [
    {
        "id": 1, "timestamp": 1, "severity": "info", "type": "Cycloid",
        "title": "A component has been created",
        "tags": [{"key": "action", "value": "create"}, {"key": "entity", "value": "component"}],
    },
    {
        "id": 2, "timestamp": 2, "severity": "info", "type": "Cycloid",
        "title": "A component has been deleted",
        "tags": [{"key": "action", "value": "delete"}, {"key": "entity", "value": "component"}],
    },
    {
        "id": 3, "timestamp": 3, "severity": "info", "type": "Cycloid",
        "title": "A build has been created",
        "tags": [{"key": "action", "value": "create"}, {"key": "entity", "value": "ci_build"}],
    },
    {
        "id": 4, "timestamp": 4, "severity": "info", "type": "Cycloid",
        "title": "A component has been configured",
        "tags": [{"key": "action", "value": "configure"}, {"key": "entity", "value": "component"}],
    },
]


@pytest.fixture
def event_server() -> FastMCP:
    """Create a test MCP server with event components."""
    server: FastMCP = FastMCP("TestEventServer")
    server.add_tool(list_events)
    server.add_tool(list_project_events)
    server.add_resource(get_events_resource)
    return server


class TestEventComponent:
    """Test event component functionality."""

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_json(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Test event listing returns JSON dict with full payload including tags."""
        mock_execute_cli.return_value = [SAMPLE_EVENT]

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_EVENT_LIST",
                {"severity": ["info"], "type": ["Cycloid"]},
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)
            assert data["count"] == 1
            assert data["events"][0]["severity"] == "info"
            assert data["events"][0]["tags"] == SAMPLE_EVENT["tags"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_filter_by_action(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """`action` narrows events to those whose action tag matches."""
        mock_execute_cli.return_value = FILTER_EVENTS

        async with Client(event_server) as client:
            result = await client.call_tool("CYCLOID_EVENT_LIST", {"action": ["delete"]})
            data = json.loads(result.content[0].text)
            assert data["count"] == 1
            assert data["events"][0]["id"] == 2

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_filter_by_entity(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """`entity` narrows events to those whose entity tag matches (e.g. ci_build)."""
        mock_execute_cli.return_value = FILTER_EVENTS

        async with Client(event_server) as client:
            result = await client.call_tool("CYCLOID_EVENT_LIST", {"entity": ["ci_build"]})
            data = json.loads(result.content[0].text)
            assert data["count"] == 1
            assert data["events"][0]["id"] == 3

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_filter_action_and_entity(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """action AND entity must both match."""
        mock_execute_cli.return_value = FILTER_EVENTS

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_EVENT_LIST",
                {"action": ["create"], "entity": ["component"]},
            )
            data = json.loads(result.content[0].text)
            assert data["count"] == 1
            assert data["events"][0]["id"] == 1

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_filter_case_insensitive(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Filter matching is case-insensitive and accepts multiple values."""
        mock_execute_cli.return_value = FILTER_EVENTS

        async with Client(event_server) as client:
            result = await client.call_tool("CYCLOID_EVENT_LIST", {"action": ["CREATE"]})
            data = json.loads(result.content[0].text)
            assert data["count"] == 2
            assert {e["id"] for e in data["events"]} == {1, 3}

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_no_filter_returns_all(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Omitting action/entity returns every event."""
        mock_execute_cli.return_value = FILTER_EVENTS

        async with Client(event_server) as client:
            result = await client.call_tool("CYCLOID_EVENT_LIST", {})
            data = json.loads(result.content[0].text)
            assert data["count"] == 4

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_filter_miss_surfaces_available_values(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """A filter that matches nothing returns the available values, not a bare 0.

        Regression for the silent `count:0` foot-gun: filtering by `build` (which
        never exists — the real tag value is `ci_build`) must surface that events
        DO exist plus the values to retry with, so callers don't report "no events".
        """
        mock_execute_cli.return_value = FILTER_EVENTS

        async with Client(event_server) as client:
            result = await client.call_tool("CYCLOID_EVENT_LIST", {"entity": ["build"]})
            data = json.loads(result.content[0].text)
            assert data["count"] == 0
            assert data["filter_matched_nothing"] is True
            assert data["applied_filters"] == {"action": None, "entity": ["build"]}
            assert data["available_entities"] == ["ci_build", "component"]
            assert data["available_actions"] == ["configure", "create", "delete"]
            assert "ci_build" in data["hint"] or "available" in data["hint"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_matching_filter_has_no_diagnostic(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """A filter that DOES match must not include the miss diagnostic."""
        mock_execute_cli.return_value = FILTER_EVENTS

        async with Client(event_server) as client:
            result = await client.call_tool("CYCLOID_EVENT_LIST", {"entity": ["ci_build"]})
            data = json.loads(result.content[0].text)
            assert data["count"] == 1
            assert "filter_matched_nothing" not in data

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_empty_window_has_no_diagnostic(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """When the CLI itself returns nothing, no filter diagnostic is emitted."""
        mock_execute_cli.return_value = []

        async with Client(event_server) as client:
            result = await client.call_tool("CYCLOID_EVENT_LIST", {"entity": ["ci_build"]})
            data = json.loads(result.content[0].text)
            assert data["count"] == 0
            assert "filter_matched_nothing" not in data

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_events_resource(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Test events resource."""
        mock_execute_cli.return_value = [
            {
                "id": 2,
                "timestamp": 1234567891000,
                "severity": "warn",
                "type": "AWS",
                "title": "Another event",
                "message": "Something",
                "tags": [{"key": "user", "value": "bob"}],
            }
        ]

        async with Client(event_server) as client:
            result = await client.read_resource("cycloid://events")

            if hasattr(result, "content") and result.content:
                text_content: str = result.content[0].text
            elif hasattr(result, "__iter__") and len(result) > 0:  # type: ignore[arg-type]
                text_content = result[0].text  # type: ignore[index]
            else:
                text_content = str(result)

            data = json.loads(text_content)
            assert data["count"] == 1
            assert data["events"][0]["type"] == "AWS"

    async def test_event_tools_registered(self, event_server: FastMCP) -> None:
        """Test that event tools are registered."""
        async with Client(event_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]
            assert "CYCLOID_EVENT_LIST" in tool_names
            assert "CYCLOID_PROJECT_EVENTS" in tool_names

    async def test_event_resources_registered(self, event_server: FastMCP) -> None:
        """Test that event resources are registered."""
        async with Client(event_server) as client:
            resources = await client.list_resources()
            resource_uris: List[str] = [str(resource.uri) for resource in resources]
            assert "cycloid://events" in resource_uris


class TestProjectEventsComponent:
    """Tests for CYCLOID_PROJECT_EVENTS tool."""

    def _make_mock(self, envs: list, components_per_env: list, events: list) -> MagicMock:
        """Build a mock execute_cli that returns envs, then per-env components, then events."""
        call_count = 0

        async def side_effect(  # type: ignore[assignment]
            subcommand: str, args: list, flags: dict = None, **kwargs,
        ):
            nonlocal call_count
            call_count += 1
            if subcommand == "project" and args == ["list-env"]:
                return envs
            if subcommand == "components" and args == ["list"]:
                env_canonical = (flags or {}).get("env", "")
                for i, env in enumerate(envs):
                    if env.get("canonical") == env_canonical:
                        return components_per_env[i] if i < len(components_per_env) else []
                return []
            if subcommand == "event" and args == ["list"]:
                return events
            return []

        mock = MagicMock()
        mock.side_effect = side_effect
        return mock

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_project_events_scoped_to_project(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Events are filtered to only those with matching project tag."""
        envs = [{"canonical": "prod"}, {"canonical": "staging"}]
        components_per_env = [
            [{"canonical": "api"}],
            [{"canonical": "worker"}],
        ]
        all_events = [SAMPLE_EVENT, SAMPLE_EVENT_OTHER_PROJECT, SAMPLE_EVENT_NO_PROJECT_TAG]

        mock_execute_cli.side_effect = self._make_mock(
            envs, components_per_env, all_events,
        ).side_effect

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_EVENTS",
                {"project": "awesome-project"},
            )
            result_text: str = result.content[0].text
            data = json.loads(result_text)

            assert data["count"] == 1
            assert data["events"][0]["id"] == 1
            assert data["project"] == "awesome-project"
            # Actor extracted from tags[key=user]
            assert len(data["actors"]) == 1
            assert data["actors"][0]["username"] == "alice"

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_project_events_filter_by_action(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """`action` narrows project events (applied after project-tag scoping)."""
        envs = [{"canonical": "prod"}]
        components_per_env = [[{"canonical": "api"}]]
        all_events = [
            {
                "id": 10, "timestamp": 1, "severity": "info", "type": "Cycloid",
                "title": "A component has been deleted",
                "tags": [
                    {"key": "project", "value": "p1"},
                    {"key": "action", "value": "delete"},
                    {"key": "entity", "value": "component"},
                ],
            },
            {
                "id": 11, "timestamp": 2, "severity": "info", "type": "Cycloid",
                "title": "A component has been created",
                "tags": [
                    {"key": "project", "value": "p1"},
                    {"key": "action", "value": "create"},
                    {"key": "entity", "value": "component"},
                ],
            },
        ]

        mock_execute_cli.side_effect = self._make_mock(
            envs, components_per_env, all_events,
        ).side_effect

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_EVENTS",
                {"project": "p1", "action": ["delete"]},
            )
            data = json.loads(result.content[0].text)
            assert data["count"] == 1
            assert data["events"][0]["id"] == 10

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_project_events_filter_miss_surfaces_available_values(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """A non-matching filter on project events surfaces the available values.

        The project HAS events, but `entity=['build']` (non-existent; real value is
        `ci_build`) matches none — so the response must list the values to retry with
        rather than implying the project has no activity.
        """
        envs = [{"canonical": "prod"}]
        components_per_env = [[{"canonical": "api"}]]
        all_events = [
            {
                "id": 20, "timestamp": 1, "severity": "info", "type": "Cycloid",
                "title": "A build has been created",
                "tags": [
                    {"key": "project_canonical", "value": "p1"},
                    {"key": "action", "value": "create"},
                    {"key": "entity", "value": "ci_build"},
                ],
            },
        ]
        mock_execute_cli.side_effect = self._make_mock(
            envs, components_per_env, all_events,
        ).side_effect

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_EVENTS",
                {"project": "p1", "entity": ["build"]},
            )
            data = json.loads(result.content[0].text)
            assert data["count"] == 0
            assert data["filter_matched_nothing"] is True
            assert data["available_entities"] == ["ci_build"]
            assert data["available_actions"] == ["create"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_project_events_cap_exceeded(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Returns structured error when total components exceed the cap."""
        # 55 unique components spread across 2 envs
        envs = [{"canonical": "prod"}, {"canonical": "staging"}]
        components_prod = [{"canonical": f"prod-comp-{i}"} for i in range(30)]
        components_staging = [{"canonical": f"staging-comp-{i}"} for i in range(25)]

        mock_execute_cli.side_effect = self._make_mock(
            envs, [components_prod, components_staging], []
        ).side_effect

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_EVENTS",
                {"project": "big-project"},
            )
            result_text: str = result.content[0].text
            data = json.loads(result_text)

            assert "error" in data
            assert data["total_components"] == 55
            assert data["max_components"] == 50
            assert "big-project" in data["error"]
            assert "CYCLOID_PROJECT_EVENTS_MAX_COMPONENTS" in data["error"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_project_events_no_envs(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Returns count=0 with no error when project has no environments."""
        mock_execute_cli.side_effect = self._make_mock([], [], []).side_effect

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_EVENTS",
                {"project": "empty-project"},
            )
            result_text: str = result.content[0].text
            data = json.loads(result_text)

            assert data["count"] == 0
            assert data["events"] == []
            assert "error" not in data

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_project_events_deduplicates_actors(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Actors list is deduplicated when same user appears in multiple events."""
        envs = [{"canonical": "prod"}]
        components = [{"canonical": "api"}]
        events = [
            {
                "id": 10, "timestamp": 1000, "severity": "info", "type": "Cycloid",
                "title": "Event A", "message": "msg",
                "tags": [
                    {"key": "project", "value": "myproject"},
                    {"key": "user", "value": "alice"},
                ],
            },
            {
                "id": 11, "timestamp": 1001, "severity": "info", "type": "Cycloid",
                "title": "Event B", "message": "msg",
                "tags": [
                    {"key": "project", "value": "myproject"},
                    {"key": "user", "value": "alice"},
                ],
            },
            {
                "id": 12, "timestamp": 1002, "severity": "info", "type": "Cycloid",
                "title": "Event C", "message": "msg",
                "tags": [{"key": "project", "value": "myproject"}, {"key": "user", "value": "bob"}],
            },
        ]
        mock_execute_cli.side_effect = self._make_mock(envs, [components], events).side_effect

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_EVENTS",
                {"project": "myproject"},
            )
            result_text: str = result.content[0].text
            data = json.loads(result_text)

            assert data["count"] == 3
            usernames = [a["username"] for a in data["actors"]]
            assert sorted(usernames) == ["alice", "bob"]
            assert len(usernames) == 2  # deduplicated

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_project_events_matches_project_canonical_tag(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Live Cycloid platform events tag only `project_canonical`, not `project`.

        Regression for the bug where activity tab showed events for a project
        but `CYCLOID_PROJECT_EVENTS` returned `[]` because the filter only
        matched the legacy `project` tag key.
        """
        envs = [{"canonical": "us"}]
        components = [{"canonical": "aws"}]
        events = [
            {
                "id": 781083,
                "timestamp": 1779721716814,
                "severity": "info",
                "type": "Cycloid",
                "title": "A build has been created",
                "message": "...",
                "tags": [
                    {"key": "action", "value": "create"},
                    {"key": "entity", "value": "ci_build"},
                    {"key": "pipeline_name", "value": "cycloid-saas-us"},
                    {"key": "project_canonical", "value": "cycloid-saas"},
                    {"key": "environment_canonical", "value": "us"},
                    {"key": "member_id", "value": "1232"},
                    {"key": "component_canonical", "value": "aws"},
                    {"key": "organization_canonical", "value": "cycloid"},
                ],
            },
            {
                "id": 781078,
                "timestamp": 1779719540239,
                "severity": "info",
                "type": "Cycloid",
                "title": "A build has been created",
                "message": "...",
                "tags": [
                    {"key": "project_canonical", "value": "cycloid-saas"},
                    {"key": "member_id", "value": "18"},
                    {"key": "action", "value": "create"},
                ],
            },
        ]
        mock_execute_cli.side_effect = self._make_mock(envs, [components], events).side_effect

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_EVENTS",
                {"project": "cycloid-saas"},
            )
            data = json.loads(result.content[0].text)
            assert data["count"] == 2, f"expected both events matched, got {data}"
            # member_id-based actors expose numeric id, not username
            ids = sorted(a.get("id", "") for a in data["actors"])
            assert ids == ["1232", "18"]
            assert all("username" not in a for a in data["actors"])
