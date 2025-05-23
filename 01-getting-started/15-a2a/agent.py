from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import file_write
import os
import json
import asyncio


class StrandAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.agent = None

        try:
            os.makedirs("sessions", exist_ok=True)
            self.documentation_mcp_server = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="uvx",
                        args=["awslabs.aws-documentation-mcp-server@latest"],
                    )
                )
            )
            self.documentation_mcp_server.start()
            self.tools = self.documentation_mcp_server.list_tools_sync() + [file_write]

        except Exception as e:
            return f"Error initializing agent: {str(e)}"

    def _load_agent_from_memory(self, session_id: str) -> str:
        session_path = os.path.join("sessions", f"{session_id}.json")
        agent = None

        try:
            if os.path.isfile(session_path):
                with open(session_path, "r") as f:
                    state = json.load(f)

                agent = Agent(
                    messages=state["messages"],
                    system_prompt=state["system_prompt"],
                    tools=self.tools,
                    callback_handler=None,
                )
            else:
                agent = Agent(
                    system_prompt="""You are a thorough AWS researcher specialized in finding accurate 
                    information online. For each question:
                    
                    1. Determine what information you need
                    2. Search the AWS Documentation for reliable information
                    3. Extract key information and cite your sources
                    4. Store important findings in memory for future reference
                    5. Synthesize what you've found into a clear, comprehensive answer
                    
                    When researching, focus only on AWS documentation. Always provide citations 
                    for the information you find.
                    
                    Finally output your response to a file in current directory.
                    """,
                    tools=self.tools,
                    callback_handler=None,
                )
            return agent
        except Exception as e:
            raise f"Error Loading agent from memory: {e}"

    def _store_agent_into_memory(self, agent: Agent, session_id: str) -> bool:
        session_path = os.path.join("sessions", f"{session_id}.json")
        state = {"messages": agent.messages, "system_prompt": agent.system_prompt}
        with open(session_path, "w") as f:
            json.dump(state, f)
        return True

    async def stream(self, query: str, session_id: str):
        agent = self._load_agent_from_memory(session_id=session_id)
        response = str()
        try:
            async for event in agent.stream_async(query):
                if "data" in event:
                    # Only stream text chunks to the client
                    response += event["data"]
                    yield {
                        "is_task_complete": "complete" in event,
                        "require_user_input": False,
                        "content": event["data"],
                    }

        except Exception as e:
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"We are unable to process your request at the moment. Error: {e}",
            }
        finally:
            self._store_agent_into_memory(agent, session_id)
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }

    def invoke(self, query: str, session_id: str):
        agent = self._load_agent_from_memory(session_id=session_id)
        try:
            response = str(agent(query))

            self._store_agent_into_memory(agent, session_id)

        except Exception as e:
            raise f"Error invoking agent: {e}"
        return response


async def main():
    agent = StrandAgent()

    async for chunk in agent.stream("hello", "123"):
        print(chunk, "")


if __name__ == "__main__":
    asyncio.run(main())
