"""Stack handler for Cycloid MCP server."""

import json
from typing import Any, Dict, List, Optional

import structlog
from mcp.types import Prompt, TextContent

from ..cli_mixin import CLIMixin
from ..exceptions import CycloidCLIError

logger = structlog.get_logger(__name__)


class StackHandler(CLIMixin):
    """Handler for stack creation operations."""

    def __init__(self):
        """Initialize the stack handler."""
        super().__init__()

    def get_prompts(self) -> List[Prompt]:
        """Get available prompts."""
        return [
            Prompt(
                name="cycloid_stack_create_from_blueprint",
                title="Create Cycloid Stack from Blueprint",
                description="Guided workflow to create a new Cycloid Terraform stack from a blueprint",
                prompt="""# Create Cycloid Stack from Blueprint

This guided workflow will help you create a new Cycloid Terraform stack from a blueprint.

## Step 1: Select Blueprint

First, let's explore available blueprints. You can choose from:

- **cycloid-stacks**: Main Cycloid stacks repository
- **cycloid-demo-stacks**: Demo stacks repository  
- **stack-getting-started**: Getting started examples
- **terraform-runner**: Terraform automation templates

## Step 2: Choose Use Case

Select your use case:
- **AWS**: Amazon Web Services infrastructure
- **Azure**: Microsoft Azure infrastructure
- **GCP**: Google Cloud Platform infrastructure
- **vanilla**: Generic infrastructure

## Step 3: Provide Details

- **Stack Name**: A unique name for your stack
- **Service Catalog Source**: The repository containing your blueprint

## Step 4: Confirmation

Review your choices and confirm the stack creation.

Would you like to start this workflow? I can help you through each step.""",
            )
        ]

    async def get_prompt(self, name: str) -> Optional[Prompt]:
        """Get a specific prompt."""
        if name == "cycloid_stack_create_from_blueprint":
            return Prompt(
                name=name,
                title="Create Cycloid Stack from Blueprint",
                description="Guided workflow to create a new Cycloid Terraform stack from a blueprint",
                prompt=self._get_stack_creation_prompt(),
            )
        return None

    def _get_stack_creation_prompt(self) -> str:
        """Get the stack creation prompt content."""
        return """# Create Cycloid Stack from Blueprint

This guided workflow will help you create a new Cycloid Terraform stack from a blueprint.

## Available Blueprints

Let me show you the available service catalog repositories and their blueprints:

### Popular Choices:

1. **cycloid-stacks** - Main Cycloid stacks repository
   - Contains production-ready infrastructure templates
   - Well-tested and maintained blueprints

2. **cycloid-demo-stacks** - Demo stacks repository
   - Great for learning and testing
   - Simple examples to get started

3. **stack-getting-started** - Getting started examples
   - Perfect for beginners
   - Step-by-step tutorials

4. **terraform-runner** - Terraform automation templates
   - CI/CD focused blueprints
   - Automation and deployment templates

## Use Cases

Choose your target platform:
- **AWS**: Amazon Web Services infrastructure
- **Azure**: Microsoft Azure infrastructure  
- **GCP**: Google Cloud Platform infrastructure
- **vanilla**: Generic infrastructure (works with any provider)

## Required Information

To create your stack, I'll need:
1. **Blueprint Reference**: The specific blueprint to use
2. **Stack Name**: A unique name for your stack
3. **Use Case**: Your target platform (AWS, Azure, GCP, vanilla)
4. **Service Catalog Source**: The repository containing the blueprint

## Next Steps

Would you like me to:
1. Show you available blueprints from a specific repository?
2. Help you choose a use case?
3. Start the stack creation process with specific details?

Just let me know how you'd like to proceed!"""

    async def execute_stack_creation(
        self, 
        blueprint_ref: str = "",
        name: str = "",
        use_case: str = "",
        service_catalog_source_canonical: str = "",
        confirm: str = ""
    ) -> str:
        """Execute the stack creation workflow."""
        try:
            # Validate inputs
            if not blueprint_ref:
                return "❌ Error: Blueprint reference is required"
            
            if not name:
                return "❌ Error: Stack name is required"
            
            if not use_case:
                return "❌ Error: Use case is required"
            
            if not service_catalog_source_canonical:
                return "❌ Error: Service catalog source is required"

            # Execute the stack creation command
            result = await self.execute_cli_json(
                "stack", ["create", "from-blueprint"],
                flags={
                    "blueprint-ref": blueprint_ref,
                    "name": name,
                    "use-case": use_case,
                    "service-catalog-source-canonical": service_catalog_source_canonical,
                    "confirm": confirm.lower() == "true" if confirm else True
                }
            )

            return f"""✅ Stack creation initiated successfully!

**Stack Details:**
- Name: {name}
- Blueprint: {blueprint_ref}
- Use Case: {use_case}
- Source: {service_catalog_source_canonical}

The stack creation process has been started. You can monitor its progress in the Cycloid console.

**Next Steps:**
1. Check the stack status in your Cycloid dashboard
2. Review the generated Terraform configuration
3. Apply the stack when ready

Stack ID: {result.get('id', 'N/A')}"""

        except CycloidCLIError as e:
            logger.error(
                "Failed to create stack from blueprint",
                error=str(e),
                blueprint_ref=blueprint_ref,
                name=name,
                use_case=use_case,
            )
            return f"❌ Error creating stack: {str(e)}" 