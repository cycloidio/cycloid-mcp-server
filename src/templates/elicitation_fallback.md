# Interactive Elicitation Not Supported

🚨 **CRITICAL**: The client doesn't support interactive elicitation. The LLM should NEVER guess or assume parameter values. ALL parameters must be explicitly provided by the user.

⚠️ **LLM INSTRUCTIONS**: Do NOT provide default values, suggestions, or examples. Let the user make their own choices. Do NOT call this tool with guessed parameters.

## Blueprint Details
- **Name**: {name}
- **Description**: {description}
- **Version**: {version}

## Available Use Cases
{use_cases}

## Available Service Catalog Sources
{canonicals}

## How to Create the Stack

Since interactive elicitation is not supported, you'll need to provide all parameters when calling this tool again. Here are the required parameters:

### Required Parameters
- `ref`: {ref} (already provided)
- `name`: Choose a name for your stack (YOU must choose this)
- `use_case`: Choose one from: {use_cases} (YOU must choose this)
- `service_catalog_source_canonical`: Choose from: {canonicals} (YOU must choose this)

## ⚠️ IMPORTANT FOR LLM
- Do NOT provide example values in your response
- Do NOT suggest specific use cases or catalog sources
- Do NOT call this tool with guessed parameters
- Let the user provide their own choices
- Only call this tool when the user explicitly provides ALL required parameters

## Next Steps
1. Choose your preferred use case from the list above
2. Choose your preferred service catalog source from the list above
3. Decide on a name for your stack
4. Call this tool again with all the required parameters

**🚨 REMINDER**: The LLM should NEVER guess or provide default values!
