import asyncio
from typing import Dict, List
from termcolor import colored
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import swarm

init_message_created = False

class SQLAgent:
    def __init__(self):
        # Step 1: Define system prompt
        self.system_prompt = """You are a Text-to-SQL agent. You will be given a natural language query
                and you have to generate valid SQL for it. Use the tools at your disposal to do the following tasks:
                    - Generate a SQL Query using swarm of 3 agents
                    - Execute the SQL query on the database
                    - If error occurs while execution, take the error message into consideration and rewrite the SQL query
                    - Respond with SQL response
                
                If valid SQL cannot be generate from query please simply reply "Valid SQL cannot be generated". 
                
                Only respond with SQL execution response. Format the data properly using Markdown.
                """
        
        # Step 2: Initialize tools
        self.tools = []
        try:
            self.sql_mcp_server = MCPClient(lambda: sse_client("http://localhost:8000/sse"))
            self.sql_mcp_server.start()
            self.tools = self.sql_mcp_server.list_tools_sync() + [swarm]
        except Exception as e:
            raise f"Error initializing tools: {str(e)}"

        # Step 3: Initialize agent
        try:
            self.agent = Agent(
                    system_prompt=self.system_prompt,
                    tools=self.tools,
                )
        except Exception as e:
            raise f"Error initializing agent: {str(e)}"
        
        # Step 4: Initialize messages
        try:
            self.agent.messages = self._create_initial_messages()
        except Exception as e:
            raise f"Error initializing messages: {str(e)}"

    def _create_initial_messages(self) -> List[Dict]:
        """Create initial conversation messages."""
        schema = self.sql_mcp_server.call_tool_sync(
            tool_use_id="tool_get_schema_5234",
            name="get_schema",
        )
        return [
            {"role": "user", "content": [{"text": "Hello, can I get database schema?"}]},
            {"role": "assistant", "content": [{"text": f"Database schema: {schema}"}]},
        ]
    
    async def invoke(self, query: str):
        response = str()
        try:
            async for event in self.agent.stream_async(query):
                if "data" in event:
                    # Only stream text chunks to the client
                    response += event["data"]
        except Exception as e:
            raise f"error processing your request: {e}"
        
        return response

if __name__ == "__main__":
    print("\n📁 SQL Assistant\n")
    print("You can try following queries:")
    print("- How many average vacations are left amoung all employees?")
    print("- Can you list all employee information?")
    print("- How many vaccations all employess have left?")
    print("Type 'exit' to quit.")
    
    sql_assistant = SQLAgent()

    # Interactive loop
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break
            
            response = asyncio.run(sql_assistant.invoke(user_input))
            print(colored(response, "green"))

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try asking a different question.")
        
