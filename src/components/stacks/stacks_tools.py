"""Stacks MCP tools."""

from typing import Any, Dict, List, Tuple
from fastmcp import Context

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin

from .stacks_handler import StackHandler

logger = get_logger(__name__)





class StackCreationElicitor:
    """Handles the interactive elicitation flow for stack creation."""

    def __init__(self, handler: StackHandler):
        super().__init__()
        self.handler = handler

    async def elicit_stack_parameters(
        self, ctx: Any, ref: str, available_use_cases: List[str]
    ) -> Tuple[bool, str, Dict[str, str]]:
        """Elicit all required stack parameters from the user."""
        try:
            # Get stack name
            name_success, name_result = await self._elicit_stack_name(ctx)
            if not name_success:
                return False, name_result, {}

            # Get use case
            use_case_success, use_case_result = await self._elicit_use_case(
                ctx, available_use_cases
            )
            if not use_case_success:
                return False, use_case_result, {}

            # Get service catalog source
            catalog_success, catalog_result = await self._elicit_service_catalog_source(ctx)
            if not catalog_success:
                return False, catalog_result, {}

            # Confirm creation
            confirm_success, confirm_result = await self._confirm_stack_creation(
                ctx, ref, name_result, use_case_result, catalog_result
            )
            if not confirm_success:
                return False, confirm_result, {}

            return True, "", {
                "name": name_result,
                "use_case": use_case_result,
                "service_catalog_source_canonical": catalog_result,
            }

        except Exception as elicitation_error:
            fallback_log = f"Elicitation not supported or failed: {str(elicitation_error)}"
            logger.info(fallback_log)
            return False, "ELICITATION_FAILED", {}

    async def _elicit_stack_name(self, ctx: Context) -> Tuple[bool, str]:
        """Elicit stack name from user."""
        logger.info("🚀 DEBUG: _elicit_stack_name called")
        logger.info(f"🚀 DEBUG: ctx type in _elicit_stack_name: {type(ctx)}")

        try:
            # Get stack name - let the user choose, don't suggest or assume
            stack_name_prompt = (
                "What would you like to name your stack? "
            )
            logger.info("🚀 DEBUG: About to call ctx.elicit for stack name")
            stack_name_result = await ctx.elicit(stack_name_prompt, response_type=str)
            stack_name_log = (
                f"Stack name elicitation result: action="
                f"{stack_name_result.action}"
            )
            # Safely access data attribute
            try:
                data_value = getattr(stack_name_result, 'data', None)
                if data_value is not None:
                    stack_name_log += f", data={data_value}"
            except Exception:
                pass
            logger.info(stack_name_log)

            if stack_name_result.action != "accept":
                return False, "Stack creation cancelled - no stack name provided."

            # Safely get data value
            try:
                data_value = getattr(stack_name_result, 'data', None)
                if not data_value:
                    return False, "❌ Stack name cannot be empty. Please provide a valid name."
                stack_name = str(data_value).strip()
                if not stack_name:
                    return False, "❌ Stack name cannot be empty. Please provide a valid name."
            except Exception:
                return False, "❌ Stack name cannot be empty. Please provide a valid name."

            return True, stack_name

        except AttributeError as e:
            logger.info(f"Elicitation not supported: {str(e)}")
            return False, "ELICITATION_NOT_SUPPORTED"
        except Exception as e:
            logger.info(f"Elicitation failed: {str(e)}")
            return False, "ELICITATION_FAILED"

    async def _elicit_use_case(self, ctx: Context, available_use_cases: List[str]) -> Tuple[bool, str]:
        """Elicit use case from user."""
        # Get use case - present options but let user choose
        use_case_prompt = (
            f"Which use case would you like to use? "
            f"Available options: {', '.join(available_use_cases)}\n\n"
        )
        use_case_result = await ctx.elicit(use_case_prompt, response_type=available_use_cases)
        use_case_log = (
            f"Use case elicitation result: action="
            f"{use_case_result.action}, "
            f"data={use_case_result.data}"
        )
        logger.info(use_case_log)

        if use_case_result.action != "accept":
            return False, "Stack creation cancelled - no use case provided."

        use_case = use_case_result.data

        # Validate that the selected use case is actually available
        if use_case not in available_use_cases:
            available_str = ", ".join(available_use_cases)
            return False, (
                f"❌ Invalid use case '{use_case}'. "
                f"Available options are: {available_str}"
            )

        return True, use_case

    async def _elicit_service_catalog_source(self, ctx: Context) -> Tuple[bool, str]:
        """Elicit service catalog source from user."""
        # Get available catalog repositories to fetch valid canonical options
        logger.info("Fetching catalog repositories to get valid canonical options")
        try:
            catalog_repositories = await self.handler.get_catalog_repositories()
            available_canonicals = self.handler.get_available_canonicals(catalog_repositories)
        except Exception as e:
            error_msg = f"Failed to fetch catalog repositories: {str(e)}"
            logger.error(error_msg)
            return False, f"❌ {error_msg}"

        if not available_canonicals:
            return False, "❌ No catalog repositories found. Please check your configuration."

        logger.info(f"Found catalog repositories with canonicals: {available_canonicals}")

        # Get service catalog source canonical - present only valid options
        service_catalog_prompt = (
            f"Which service catalog source should I use? "
            f"Available options: {', '.join(available_canonicals)}\n\n"
        )
        service_catalog_result = await ctx.elicit(
            service_catalog_prompt, response_type=available_canonicals
        )
        service_catalog_log = (
            f"Service catalog elicitation result: action="
            f"{service_catalog_result.action}, "
            f"data={service_catalog_result.data}"
        )
        logger.info(service_catalog_log)

        if service_catalog_result.action != "accept":
            return False, "Stack creation cancelled - no service catalog source provided."

        service_catalog_source_canonical = service_catalog_result.data

        # Validate that the selected canonical is actually available
        if service_catalog_source_canonical not in available_canonicals:
            available_str = ", ".join(available_canonicals)
            return False, (
                f"❌ Invalid service catalog source '{service_catalog_source_canonical}'. "
                f"Available options are: {available_str}"
            )

        return True, service_catalog_source_canonical

    async def _confirm_stack_creation(
        self, ctx: Context, ref: str, name: str, use_case: str, service_catalog_source_canonical: str
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
        confirmation_log = (
            f"Confirmation elicitation result: action="
            f"{confirmation_result.action}, "
            f"data={confirmation_result.data}"
        )
        logger.info(confirmation_log)

        if confirmation_result.action != "accept":
            return False, "Stack creation cancelled by user."

        # Check if the user confirmed
        if confirmation_result.data.lower() != "confirm":
            return False, "Stack creation cancelled - user did not type 'confirm'."

        return True, ""


class StackTools(MCPMixin):
    """Tools for working with Cycloid Stacks."""

    def __init__(self, cli: CLIMixin):
        """Initialize stacks tools with CLI mixin."""
        super().__init__()
        self.handler = StackHandler(cli)
        self.elicitor = StackCreationElicitor(self.handler)

    @mcp_tool(
        name="CYCLOID_BLUEPRINT_LIST",
        description=(
            "List all available blueprints with their details. "
            "The LLM can filter the results based on user requirements."
        ),
        enabled=True,
    )
    async def list_blueprints(self, format: str = "table") -> str | Dict[str, Any]:
        """List all available blueprints.

        This tool provides access to all blueprints with their details.
        The LLM can filter the results based on user requirements.

        Args:
            format: Output format ("table" or "json")
        """
        try:
            # Get blueprints using shared logic
            blueprints = await self.handler.get_blueprints()

            # Format output
            if format == "json":
                result = {"blueprints": blueprints, "count": len(blueprints)}
                return result
            else:
                table_result = self.handler.format_blueprint_table_output(blueprints, "")
                return table_result

        except Exception as e:
            error_msg = f"❌ Error listing blueprints: {str(e)}"
            logger.error("Error listing blueprints", extra={"error": str(e)})
            return error_msg

    async def _validate_blueprint(self, ref: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate blueprint and return success status, error message, and blueprint data."""
        logger.info(f"Fetching blueprint details for ref: {ref}")
        blueprints = await self.handler.get_blueprints()

        # Find the specific blueprint by ref
        blueprint = self.handler.get_blueprint_by_ref(blueprints, ref)

        if not blueprint:
            return False, (
                f"❌ Blueprint '{ref}' not found. Please check the blueprint reference."
            ), {}

        # Get available use cases from the blueprint
        available_use_cases = blueprint.get("use_cases", [])
        if not available_use_cases:
            return False, (
                f"❌ No use cases found for blueprint '{ref}'. "
                f"This blueprint may not be properly configured."
            ), {}

        logger.info(f"Found use cases for blueprint {ref}: {available_use_cases}")
        return True, "", blueprint

    async def _handle_direct_creation(
        self,
        ref: str,
        name: str,
        use_case: str,
        service_catalog_source_canonical: str,
        available_use_cases: List[str],
    ) -> str:
        """Handle direct stack creation when all parameters are provided."""
        logger.info("All parameters provided, proceeding with direct stack creation")
        return await self.handler.create_stack_directly(
            ref, name, use_case, service_catalog_source_canonical,
            available_use_cases
        )

    async def _handle_no_elicitation(
        self, ref: str, blueprint: Dict[str, Any]
    ) -> str:
        """Handle case when elicitation is not available."""
        # Get available catalog repositories for guidance
        try:
            catalog_repositories = await self.handler.get_catalog_repositories()
            available_canonicals = self.handler.get_available_canonicals(catalog_repositories)
        except Exception as e:
            error_msg = f"Failed to fetch catalog repositories: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"

        return self.handler.create_guidance_message(
            ref, blueprint, available_canonicals
        )

    async def _execute_stack_creation(
        self, ref: str, name: str, use_case: str, service_catalog_source_canonical: str
    ) -> str:
        """Execute the actual stack creation command."""
        # Generate canonical (slug) from name
        canonical = self.handler.generate_canonical_from_name(name)

        args = [
            "create",
            "--blueprint-ref", ref,
            "--name", name,
            "--stack", canonical,
            "--use-case", use_case,
            "--catalog-repository", service_catalog_source_canonical,
        ]
        # Filter out None values (though they shouldn't be None in this context)
        args = [arg for arg in args if arg]

        result = await self.handler.cli.execute_cli_command("stack", args)

        if result.exit_code == 0:
            success_msg = f"✅ Stack '{name}' created successfully!\n{result.stdout}"
            return success_msg
        else:
            error_msg = f"❌ Failed to create stack: {result.stderr}"
            return error_msg

    async def _handle_elicitation_fallback(self, ref: str, blueprint: Dict[str, Any]) -> str:
        """Handle fallback when elicitation fails."""
        try:
            catalog_repositories = await self.handler.get_catalog_repositories()
            available_canonicals = self.handler.get_available_canonicals(catalog_repositories)
        except Exception as e:
            error_msg = f"Failed to fetch catalog repositories: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"

        if not available_canonicals:
            return "❌ No catalog repositories found. Please check your configuration."

        return self.handler.create_fallback_info(
            ref, blueprint, available_canonicals
        )

    async def _handle_elicitation_flow(
        self, ctx: Context, ref: str, available_use_cases: List[str]
    ) -> str:
        """Handle the elicitation flow for stack creation."""
        try:
            logger.info("🚀 DEBUG: _handle_elicitation_flow called")
            logger.info(f"🚀 DEBUG: ctx type in elicitation flow: {type(ctx)}")
            logger.info("Attempting to use elicitation for interactive stack creation")

            # Use the elicitor to get parameters
            logger.info("🚀 DEBUG: Calling elicitor.elicit_stack_parameters")
            elicit_success, elicit_result, parameters = await self.elicitor.elicit_stack_parameters(
                ctx, ref, available_use_cases
            )
            if not elicit_success:
                logger.info(f"Elicitation failed: {elicit_result}")
                # Check if it's a specific elicitation failure marker
                if elicit_result in ["ELICITATION_FAILED", "ELICITATION_NOT_SUPPORTED"]:
                    return "ELICITATION_FAILED"
                else:
                    # This is a user cancellation or validation error
                    return elicit_result

            # Execute stack creation
            return await self._execute_stack_creation(
                ref,
                parameters["name"],
                parameters["use_case"],
                parameters["service_catalog_source_canonical"]
            )

        except Exception as elicitation_error:
            fallback_log = f"Elicitation not supported or failed: {str(elicitation_error)}"
            logger.info(fallback_log)
            # Return a special marker for elicitation failure
            return "ELICITATION_FAILED"



    @mcp_tool(
        name="CYCLOID_BLUEPRINT_STACK_CREATE",
        description=(
            "Create a new Cycloid stack from a blueprint. "
            "CRITICAL: When elicitation context (ctx) is provided, the tool will ALWAYS use "
            "interactive elicitation to ask for parameters one by one, REGARDLESS of any parameters provided. "
            "The LLM should ONLY provide the 'ref' parameter and let elicitation handle the rest. "
            "DO NOT provide name, use_case, or service_catalog_source_canonical when elicitation is available. "
            "When elicitation is not available, ALL parameters must be explicitly provided by the user. "
            "The LLM should NEVER guess or assume parameter values. "
            "🚨 CRITICAL: The LLM should NEVER provide default values, suggestions, or examples. "
            "Let the user make their own choices. Do NOT call this tool with guessed parameters."
        ),
        enabled=True,
    )
    async def create_stack_from_blueprint_smart(
        self,
        ref: str,
        name: str | None = None,
        use_case: str | None = None,
        service_catalog_source_canonical: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Create a new Cycloid stack from a blueprint.

        CRITICAL: This tool has two modes:
        
        1. **Interactive Elicitation Mode** (when ctx is provided):
           - The tool will ALWAYS use interactive elicitation, REGARDLESS of any parameters provided
           - The tool will ask for each parameter one by one (name, use_case, service_catalog_source_canonical)
           - Parameters provided in the call are COMPLETELY IGNORED when ctx is present
           - The LLM should present options but let the user make the final choice
           - DO NOT suggest or assume user preferences - let them choose
           - CORRECT USAGE: Only provide 'ref' parameter, let elicitation handle the rest
           - This ensures the user explicitly chooses each parameter
           
        2. **Direct Creation Mode** (when ctx is None):
           - ALL parameters MUST be explicitly provided by the user
           - The LLM should NEVER guess, assume, or provide default values
           - If any parameter is missing, the tool will return guidance instead of creating the stack
           - This prevents the LLM from making incorrect assumptions about user preferences
           - 🚨 CRITICAL: The LLM should NEVER provide suggestions, examples, or guessed values
           - The LLM should only call this tool when the user explicitly provides ALL required parameters

        Args:
            ctx: The FastMCP context for elicitation (optional)
            ref: The blueprint reference (e.g., "cycloid-io:terraform-sample")
            name: The name for the new stack (IGNORED when ctx is provided, REQUIRED otherwise)
            use_case: The use case to use (IGNORED when ctx is provided, REQUIRED otherwise)
            service_catalog_source_canonical: The service catalog source canonical (IGNORED when ctx is provided, REQUIRED otherwise)
        """
        # Validate blueprint first
        is_valid, error_msg, blueprint = await self._validate_blueprint(ref)
        if not is_valid:
            if ctx:
                await ctx.error(f"Blueprint validation failed: {error_msg}", extra={"ref": ref})
            return error_msg

        available_use_cases = blueprint.get("use_cases", [])
        
        if ctx:
            await ctx.info(f"Blueprint validated successfully", extra={
                "ref": ref,
                "available_use_cases": available_use_cases
            })

        # CRITICAL: When ctx is provided, ALWAYS use elicitation mode regardless of provided parameters
        if ctx is not None:
            await ctx.info(f"Starting stack creation from blueprint: {ref}")
            await ctx.info("🔍 ELICITATION MODE: Will ask for each parameter interactively")
            await ctx.info("Note: Any provided parameters will be ignored - you will be asked for each parameter")
            elicitation_result = await self._handle_elicitation_flow(ctx, ref, available_use_cases)
            if elicitation_result == "ELICITATION_FAILED":
                await ctx.error("Elicitation not supported by this client")
                # Check if parameters were provided as fallback
                if name and use_case and service_catalog_source_canonical:
                    await ctx.info("Using provided parameters as fallback")
                    return await self._handle_direct_creation(
                        ref, name, use_case, service_catalog_source_canonical,
                        available_use_cases
                    )
                else:
                    await ctx.info("No parameters provided, showing guidance")
                    return await self._handle_no_elicitation(ref, blueprint)
            else:
                return elicitation_result
        
        # Handle direct creation mode (when ctx is None)
        if name and use_case and service_catalog_source_canonical:
            return await self._handle_direct_creation(
                ref, name, use_case, service_catalog_source_canonical,
                available_use_cases
            )
        
        # Handle no elicitation case (when ctx is None and parameters are missing)
        return await self._handle_no_elicitation(ref, blueprint)
