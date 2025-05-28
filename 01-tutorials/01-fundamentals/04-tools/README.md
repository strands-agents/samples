## Adding tools to Strands Agents

To use Tools with strands agents, you can take multiple approaches:

There are two approaches to defining python-based tools in Strands:

    - Python functions with the @tool decorator: Transform regular Python functions into tools by adding a simple decorator. This approach leverages Python's docstrings and type hints to automatically generate tool specifications.

    - Python modules following a specific format: Define tools by creating Python modules that contain a tool specification and a matching function. This approach gives you more control over the tool's definition and is useful for dependency-free implementations of tools.

Read this for more details on implementations: [Strands tools documentation](https://strandsagents.com/0.1.x/user-guide/concepts/tools/python-tools/)


### Tool Usage:
   - The tool name (function name) MUST match the file name without the extension
   - Example: For file "tool_name.py", use tool name "tool_name"

## TOOL CREATION vs. TOOL USAGE:
   - CAREFULLY distinguish between requests to CREATE a new tool versus USE an existing tool
   - When a user asks a question like "reverse hello world" or "count abc", first check if an appropriate tool already exists before creating a new one
   - If an appropriate tool already exists, use it directly instead of creating a redundant tool
   - Only create a new tool when the user explicitly requests one with phrases like "create", "make a tool", etc.

## TOOL CREATION PROCESS:
   - Name the file "tool_name.py" where "tool_name is a human readable name
   - Name the function in the file the SAME as the file name (without extension)
   - The "name" parameter in the TOOL_SPEC MUST match the name of the file (without extension)
   - Include detailed docstrings explaining the tool's purpose and parameters
   - After creating a tool, announce "TOOL_CREATED: <filename>" to track successful creation

## TOOL USAGE:
   - Use existing tools with appropriate parameters
   - Provide a clear explanation of the result

## TOOL STRUCTURE
When creating a tool, follow this exact structure:
