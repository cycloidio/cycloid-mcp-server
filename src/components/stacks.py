"""Stack/blueprint tools and resources for Cycloid MCP server."""

import json
import re
from typing import Any, Dict, List, Tuple

from fastmcp import Context
from fastmcp.dependencies import Depends  # type: ignore[reportAttributeAccessIssue]
from fastmcp.exceptions import ToolError
from fastmcp.resources import resource
from fastmcp.tools import tool
from fastmcp.utilities.logging import get_logger

from src.cli import CLIMixin, CLIResult
from src.dependencies import get_cli
from src.display_hints import build_display_hints
from src.exceptions import CycloidCLIError
from src.types import JSONList

logger = get_logger(__name__)


# --- Private helpers ---


async def _get_blueprints(cli: CLIMixin) -> JSONList:
    """Get blueprints from CLI."""
    blueprints_data = await cli.execute_cli("stacks", ["list", "--blueprint"])

    if isinstance(blueprints_data, str):
        logger.error(f"CLI returned error string: {blueprints_data}")
        return []

    return cli.process_cli_response(blueprints_data, list_key="service_catalogs")


def _get_blueprint_by_ref(
    blueprints: List[Dict[str, Any]], ref: str
) -> Dict[str, Any] | None:
    """Find a specific blueprint by reference."""
    for bp in blueprints:
        if isinstance(bp, str):
            continue
        if not isinstance(bp, dict):  # type: ignore[reportUnnecessaryIsInstance]
            continue
        if bp.get("ref") == ref:
            return bp
    return None


async def _get_catalog_repositories(cli: CLIMixin) -> List[Dict[str, Any]]:
    """Get catalog repositories for validation."""
    try:
        catalog_repositories = await cli.execute_cli("catalog-repository", ["list"])
        if isinstance(catalog_repositories, list):
            return catalog_repositories
        elif isinstance(catalog_repositories, dict):
            return catalog_repositories.get("catalog_repositories", [])
        else:
            return []
    except Exception as e:
        logger.error(f"Failed to fetch catalog repositories: {str(e)}")
        raise


def _get_available_canonicals(catalog_repositories: List[Dict[str, Any]]) -> List[str]:
    """Extract canonical values from catalog repositories."""
    available_canonicals: List[str] = []
    for repo in catalog_repositories:
        canonical = repo.get("canonical")
        if canonical:
            available_canonicals.append(str(canonical))
    return available_canonicals


def _generate_canonical_from_name(name: str) -> str:
    """Generate canonical (slug) from name."""
    canonical = re.sub(r"[^a-zA-Z0-9-]", "-", name.lower()).strip("-")
    canonical = re.sub(r"-+", "-", canonical)
    return canonical


# --- Elicitation helpers ---


async def _elicit_stack_name(ctx: Context) -> Tuple[bool, str]:
    """Elicit stack name from user."""
    try:
        stack_name_prompt = "What would you like to name your stack? "
        stack_name_result = await ctx.elicit(stack_name_prompt, response_type=str)

        if stack_name_result.action != "accept":
            return False, "Stack creation cancelled - no stack name provided."

        try:
            data_value = getattr(stack_name_result, "data", None)
            if not data_value:
                return False, "Stack name cannot be empty. Please provide a valid name."
            stack_name = str(data_value).strip()
            if not stack_name:
                return False, "Stack name cannot be empty. Please provide a valid name."
        except Exception:
            return False, "Stack name cannot be empty. Please provide a valid name."

        return True, stack_name

    except AttributeError as e:
        logger.info(f"Elicitation not supported: {str(e)}")
        return False, "ELICITATION_NOT_SUPPORTED"
    except Exception as e:
        logger.info(f"Elicitation failed: {str(e)}")
        return False, "ELICITATION_FAILED"


async def _elicit_use_case(
    ctx: Context, available_use_cases: List[str]
) -> Tuple[bool, str]:
    """Elicit use case from user."""
    use_case_prompt = (
        f"Which use case would you like to use? "
        f"Available options: {', '.join(available_use_cases)}\n\n"
    )
    use_case_result = await ctx.elicit(use_case_prompt, response_type=available_use_cases)
    logger.info(
        f"Use case elicitation result: action={use_case_result.action}, "  # noqa: E501
        + f"data={getattr(use_case_result, 'data', 'N/A')}"
    )

    if use_case_result.action != "accept":
        return False, "Stack creation cancelled - no use case provided."

    use_case = getattr(use_case_result, "data", str(use_case_result))

    if use_case not in available_use_cases:
        available_str = ", ".join(available_use_cases)
        return False, (
            f"Invalid use case '{use_case}'. Available options are: {available_str}"
        )

    return True, use_case


async def _elicit_service_catalog_source(
    ctx: Context, cli: CLIMixin
) -> Tuple[bool, str]:
    """Elicit service catalog source from user."""
    logger.info("Fetching catalog repositories to get valid canonical options")
    try:
        catalog_repositories = await _get_catalog_repositories(cli)
        available_canonicals = _get_available_canonicals(catalog_repositories)
    except Exception as e:
        return False, f"Failed to fetch catalog repositories: {str(e)}"

    if not available_canonicals:
        return False, "No catalog repositories found. Please check your configuration."

    logger.info(f"Found catalog repositories with canonicals: {available_canonicals}")

    service_catalog_prompt = (
        f"Which service catalog source should I use? "
        f"Available options: {', '.join(available_canonicals)}\n\n"
    )
    service_catalog_result = await ctx.elicit(
        service_catalog_prompt, response_type=available_canonicals
    )
    logger.info(
        f"Service catalog elicitation result: action={service_catalog_result.action}, "  # noqa: E501
        + f"data={getattr(service_catalog_result, 'data', 'N/A')}"
    )

    if service_catalog_result.action != "accept":
        return False, "Stack creation cancelled - no service catalog source provided."

    service_catalog_source_canonical = getattr(
        service_catalog_result, "data", str(service_catalog_result)
    )

    if service_catalog_source_canonical not in available_canonicals:
        available_str = ", ".join(available_canonicals)
        return False, (
            f"Invalid service catalog source '{service_catalog_source_canonical}'. "
            f"Available options are: {available_str}"
        )

    return True, service_catalog_source_canonical


async def _confirm_stack_creation(
    ctx: Context,
    ref: str,
    name: str,
    use_case: str,
    service_catalog_source_canonical: str,
) -> Tuple[bool, str]:
    """Confirm stack creation with user."""
    summary = (
        f"You are about to create a stack with the following details:\n"
        f"- Blueprint Ref: {ref}\n"
        f"- Name: {name}\n"
        f"- Use Case: {use_case}\n"
        f"- Service Catalog Source Canonical: {service_catalog_source_canonical}\n"
        "Please confirm by typing 'confirm' to proceed."
    )

    confirmation_result = await ctx.elicit(summary, response_type=["confirm"])
    logger.info(
        f"Confirmation elicitation result: action={confirmation_result.action}, "  # noqa: E501
        + f"data={getattr(confirmation_result, 'data', 'N/A')}"
    )

    if confirmation_result.action != "accept":
        return False, "Stack creation cancelled by user."

    confirmation_data = getattr(confirmation_result, "data", "")
    if str(confirmation_data).lower() != "confirm":
        return False, "Stack creation cancelled - user did not type 'confirm'."

    return True, ""


# --- Tools and Resources ---


@tool(
    name="CYCLOID_BLUEPRINT_LIST",
    description=(
        "List all available blueprints with their details. "
        "The LLM can filter the results based on user requirements. "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: name (Name), "
        "ref (Reference), description (Description), use_cases (Use Cases). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_blueprints(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List all available blueprints.

    Returns a dict with blueprints list and count.
    """
    try:
        blueprints = await _get_blueprints(cli)
        return {
            "blueprints": blueprints,
            "count": len(blueprints),
            "_display_hints": build_display_hints(
                key_fields=["name", "ref", "description", "use_cases"],
                display_format="table",
                columns={
                    "name": "Name",
                    "ref": "Reference",
                    "description": "Description",
                    "use_cases": "Use Cases",
                },
                sort_by="name",
            ),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to list blueprints: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing blueprints: {str(e)}")


@tool(
    name="CYCLOID_BLUEPRINT_STACK_CREATE",
    description=(
        "Create a new Cycloid stack from a blueprint. "
        "CRITICAL: When elicitation context (ctx) is provided, the tool will ALWAYS use "
        "interactive elicitation to ask for parameters one by one, REGARDLESS of any "
        "parameters provided. The LLM should ONLY provide the 'ref' parameter and let "
        "elicitation handle the rest. DO NOT provide name, use_case, or "
        "service_catalog_source_canonical when elicitation is available."
    ),
)
async def create_stack_from_blueprint(  # noqa: C901
    ref: str,
    ctx: Context,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> str:
    """Create a new Cycloid stack from a blueprint.

    Args:
        ref: The blueprint reference (e.g., "cycloid-io:terraform-sample")
        ctx: The FastMCP context for elicitation (injected automatically)
    """
    # Validate blueprint
    blueprints = await _get_blueprints(cli)
    blueprint = _get_blueprint_by_ref(blueprints, ref)

    if not blueprint:
        raise ToolError(f"Blueprint '{ref}' not found. Please check the blueprint reference.")

    available_use_cases = blueprint.get("use_cases", [])
    if not available_use_cases:
        raise ToolError(
            f"No use cases found for blueprint '{ref}'. "
            + "This blueprint may not be properly configured."
        )

    logger.info(f"Found use cases for blueprint {ref}: {available_use_cases}")
    await ctx.info(
        "Blueprint validated successfully",
        extra={"ref": ref, "available_use_cases": available_use_cases},
    )
    await ctx.info(f"Starting stack creation from blueprint: {ref}")

    # Elicitation flow
    try:
        # Get stack name
        name_success, name_result = await _elicit_stack_name(ctx)
        if not name_success:
            if name_result in ["ELICITATION_FAILED", "ELICITATION_NOT_SUPPORTED"]:
                return (
                    "This tool requires interactive elicitation support, which is not "
                    "available in this client. Please use a client that supports elicitation."
                )
            return name_result

        # Get use case
        use_case_success, use_case_result = await _elicit_use_case(ctx, available_use_cases)
        if not use_case_success:
            return use_case_result

        # Get service catalog source
        catalog_success, catalog_result = await _elicit_service_catalog_source(ctx, cli)
        if not catalog_success:
            return catalog_result

        # Confirm creation
        confirm_success, confirm_result = await _confirm_stack_creation(
            ctx, ref, name_result, use_case_result, catalog_result
        )
        if not confirm_success:
            return confirm_result

        # Execute stack creation
        canonical = _generate_canonical_from_name(name_result)
        args = [
            "create",
            "--blueprint-ref", ref,
            "--name", name_result,
            "--stack", canonical,
            "--use-case", use_case_result,
            "--catalog-repository", catalog_result,
        ]
        args = [arg for arg in args if arg]

        result = await cli.execute_cli_command("stack", args, auto_parse=False)

        if not isinstance(result, CLIResult) and not hasattr(result, "success"):
            raise RuntimeError("Expected CLIResult from execute_cli_command")

        cli_result = result  # type: ignore[reportUnknownMemberType]

        if cli_result.exit_code == 0:  # type: ignore[reportUnknownMemberType]
            return (
                f"Stack '{name_result}' created successfully!\n"
                f"{cli_result.stdout}"  # type: ignore[reportUnknownMemberType]
            )
        else:
            return (
                f"Failed to create stack: "
                f"{cli_result.stderr}"  # type: ignore[reportUnknownMemberType]
            )

    except Exception as elicitation_error:
        logger.info(f"Elicitation not supported or failed: {str(elicitation_error)}")
        await ctx.error("Elicitation not supported by this client")
        return (
            "This tool requires interactive elicitation support, which is not "
            "available in this client. Please use a client that supports elicitation."
        )


@resource("cycloid://blueprints")
async def get_blueprints_resource(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> str:
    """Get all available blueprints as a resource."""
    try:
        blueprints = await _get_blueprints(cli)
        result = {
            "blueprints": blueprints,
            "count": len(blueprints),
        }
        return json.dumps(result, indent=2)
    except CycloidCLIError as e:
        logger.error(f"Failed to read blueprints resource: {str(e)}")
        return json.dumps(
            {
                "error": f"Failed to load blueprints: {str(e)}",
                "blueprints": [],
                "count": 0,
            },
            indent=2,
        )
