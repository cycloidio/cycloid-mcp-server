# Stack Creation from Blueprint

The `cycloid_stack_create_from_blueprint` tool creates a new Cycloid Terraform stack from a blueprint using a **guided workflow** that helps users discover and understand the required parameters.

## Guided Workflow

The tool provides a step-by-step guided experience that helps users understand what parameters they need to provide and shows them available options.

### How to Start

Call the tool **without any parameters** to begin the guided workflow:

```bash
cycloid_stack_create_from_blueprint
```

### Workflow Steps

#### Step 1: Select a Blueprint
- Shows a table of all available blueprints with their details
- Displays name, canonical, reference, version, and description
- Provides examples and popular choices
- **User provides:** `blueprint_ref` parameter

#### Step 2: Name Your Stack
- Guides user on naming conventions and best practices
- Explains that the name will be used to identify the stack
- Provides examples of good stack names
- **User provides:** `name` parameter

#### Step 3: Select Use Case
- Shows available use cases for the selected blueprint
- Explains what each use case means (AWS, Azure, GCP, vanilla)
- **User provides:** `use_case` parameter

#### Step 4: Select Service Catalog Repository
- Lists all available service catalog repositories
- Shows popular choices with descriptions
- Handles configuration issues gracefully
- **User provides:** `service_catalog_source_canonical` parameter

#### Step 5: Review and Confirm
- Shows a summary of all selected parameters
- Displays the auto-generated canonical name
- Requires explicit confirmation to proceed
- **User provides:** `confirm: "confirm"`

## Required Parameters

| Parameter | Description | How to Find Values |
|-----------|-------------|-------------------|
| `blueprint_ref` | Blueprint reference (e.g., `cycloid-io:terraform-sample`) | Guided workflow shows available options |
| `name` | Stack name (user-defined) | User provides their desired stack name |
| `use_case` | Cloud provider or deployment type | Choose from: `aws`, `azure`, `gcp`, `vanilla` |
| `service_catalog_source_canonical` | Service catalog repository canonical name | Guided workflow shows available options |
| `confirm` | Confirmation to proceed | Must be set to `"confirm"` |

## Example Workflow

### Step 1: Start the workflow
```bash
cycloid_stack_create_from_blueprint
```
**Output:** Shows available blueprints table

### Step 2: Select blueprint
```bash
cycloid_stack_create_from_blueprint --blueprint_ref "cycloid-io:terraform-sample"
```
**Output:** Asks for stack name with guidelines

### Step 3: Provide stack name
```bash
cycloid_stack_create_from_blueprint --blueprint_ref "cycloid-io:terraform-sample" --name "my-production-stack"
```
**Output:** Shows use case options

### Step 4: Select use case
```bash
cycloid_stack_create_from_blueprint --blueprint_ref "cycloid-io:terraform-sample" --name "my-production-stack" --use_case "aws"
```
**Output:** Shows service catalog repositories

### Step 5: Select service catalog
```bash
cycloid_stack_create_from_blueprint --blueprint_ref "cycloid-io:terraform-sample" --name "my-production-stack" --use_case "aws" --service_catalog_source_canonical "cycloid-stacks"
```
**Output:** Shows summary and asks for confirmation

### Step 6: Confirm creation
```bash
cycloid_stack_create_from_blueprint --blueprint_ref "cycloid-io:terraform-sample" --name "my-production-stack" --use_case "aws" --service_catalog_source_canonical "cycloid-stacks" --confirm "confirm"
```
**Output:** Creates the stack and shows success message

## Stack Canonical Name

The tool automatically generates a canonical name (slug) from the stack name:
- Converts to lowercase
- Replaces spaces and underscores with hyphens
- Removes special characters
- Example: "My Production Stack" → "my-production-stack"

## Error Handling

- **Configuration Issues**: If Cycloid CLI is not configured, the workflow provides clear setup instructions
- **Missing Parameters**: Each step clearly shows what parameter is needed next
- **Invalid Values**: Provides helpful error messages and suggestions
- **Confirmation Required**: Prevents accidental stack creation by requiring explicit confirmation

## CLI Command Generated

The tool executes the following Cycloid CLI command:

```bash
cy stack create-from-blueprint \
  --blueprint-ref <blueprint_ref> \
  --name <name> \
  --canonical <generated_canonical> \
  --use-case <use_case> \
  --service-catalog-source-canonical <service_catalog_source_canonical> \
  --output json
```

## Prerequisites

- Cycloid CLI must be installed and configured
- Environment variables must be set: `CY_ORG`, `CY_API_KEY`
- Optionally: `CY_API_URL` for custom API endpoints

## Benefits of Guided Workflow

1. **User-Friendly**: No need to know all parameters upfront
2. **Educational**: Explains what each parameter means
3. **Discoverable**: Shows available options for each choice
4. **Safe**: Prevents errors by guiding users through valid options
5. **Flexible**: Users can modify any parameter at any step 