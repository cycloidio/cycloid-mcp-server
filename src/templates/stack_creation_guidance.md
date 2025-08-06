# Stack Creation Guidance

🚨 **CRITICAL**: Interactive elicitation is not available. You must explicitly provide ALL parameters. The LLM should NEVER guess or assume values.

⚠️ **LLM INSTRUCTIONS**: Do NOT provide default values, suggestions, or examples. Let the user make their own choices. Do NOT call this tool with guessed parameters.

To create a stack from blueprint '{ref}', you need to provide the following parameters:

## Required Parameters
- `name`: The name for your new stack (YOU must choose this)
- `use_case`: Choose from available use cases: **{use_cases}** (YOU must choose this)
- `service_catalog_source_canonical`: The service catalog source to use (YOU must choose this)

## To get available service catalog sources
Use the `CYCLOID_CATALOG_REPO_LIST` tool to see all available catalog repositories and their canonicals.

## ⚠️ IMPORTANT FOR LLM
- Do NOT provide example values in your response
- Do NOT suggest specific use cases or catalog sources
- Do NOT call this tool with guessed parameters
- Let the user provide their own choices
- Only call this tool when the user explicitly provides ALL required parameters

**Available use cases for this blueprint:** {use_cases}

## Next Steps
1. Choose your preferred use case from the list above
2. Use `CYCLOID_CATALOG_REPO_LIST` to see available catalog repositories
3. Choose your preferred catalog repository
4. Decide on a name for your stack
5. Call this tool again with ALL the required parameters

**🚨 REMINDER**: The LLM should NEVER guess or provide default values!
