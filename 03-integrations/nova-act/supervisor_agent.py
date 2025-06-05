import nova_act_agent 
from strands import Agent, tool

supervisor_agent = Agent(tools=[
    nova_act_agent.browser_automation_tool
])


if __name__ == "__main__":
    # Ask the agent a question that uses the available tools
    message = """
    I have these requests. You can run things in parallel to speed up analysis if you find it appropriate. 

    1. Get top 2 current market gainers and losers from yahoo finance 
    2. Get most recent news about these gainers and losers
    3. Create a report for the gainers and losers
    """
    supervisor_agent(message)
