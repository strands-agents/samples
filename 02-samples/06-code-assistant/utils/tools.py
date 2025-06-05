from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import editor, file_read, file_write, python_repl, shell
import os
from .prompts import CODE_AGENT_PROMPT, WRITER_AGENT_PROMPT, REVIEWER_AGENT_PROMPT

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
)

@tool
def project_reader(project_directory: str) -> dict[str, str] | str:
    """
    Read files in a project directory

    Args:
        project_directory: Project directory to read files from

    Returns:
        files content
    """
    try:
        file_reader_agent = Agent(tools=[file_read])
        return {
            file_name: file_reader_agent.tool.file_read(
                path=os.path.join(project_directory, file_name), mode="view"
            )["content"][0]["text"]
            for file_name in os.listdir(project_directory)
        }
    except Exception as e:
        return f"Error reading project {project_directory}: {e}"


@tool
def code_generator(task: str) -> str:
    """
    Generates Python code from a task description

    Args:
        task: Given task by user

    Returns:
        Generated Python code
    """
    try:
        agent = Agent(system_prompt=CODE_AGENT_PROMPT, model=bedrock_model)
        result = str(agent(f"Complete the task: {task}")).strip()
        return result or "Could not generate code. Please provide more context."
    except Exception as e:
        return f"Error generating code for task '{task}': {e}"


@tool
def code_reviewer(code: str) -> str:
    """
    Reviews Python code to a implement best practices

    Args:
        code: Python code to write.

    Returns:
        Improved Python code using best practices
    """
    try:
        agent = Agent(system_prompt=REVIEWER_AGENT_PROMPT, model=bedrock_model)
        result = str(agent(f"Optimize code:\n{code}")).strip()
        return result or "Code review did not return any result."
    except Exception as e:
        return f"Error reviewing code: {e}"


@tool
def code_writer_agent(code: str, project_name: str) -> str:
    """
    Writes Python code to a file within the specified project directory.

    Args:
        code: Python code to write.
        project_name: Name of the project directory.

    Returns:
        Confirmation message or error.
    """
    try:
        os.makedirs(f"session/{project_name}", exist_ok=True)
        agent = Agent(
            system_prompt=WRITER_AGENT_PROMPT, tools=[shell, file_write, editor]
        )
        agent(
            f"Create the files in `session/{project_name}` directory. Write the following code:\n\n{code}"
        )
        return f"Files created in session/{project_name}/ directory."
    except Exception as e:
        return f"Error writing code to file: {e}"


@tool
def code_execute(code: str) -> str:
    """
    Executes a Python code string and returns the result.

    Args:
        code: Python code to execute.

    Returns:
        Output or error message.
    """
    try:
        agent = Agent(tools=[python_repl])
        return agent.tool.python_repl(code=code)
    except Exception as e:
        return f"Error executing code: {e}"
