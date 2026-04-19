from strands import Agent
from strands.multiagent.a2a import A2AServer
from strands_tools.calculator import calculator

# Create a Strands agent with calculator tool
strands_agent = Agent(
    name="Calculator Agent",
    description="A calculator agent that can perform basic arithmetic operations.",
    tools=[calculator],
    callback_handler=None,
)

# Create A2A server
a2a_server = A2AServer(agent=strands_agent)

# Start the server
a2a_server.serve()
