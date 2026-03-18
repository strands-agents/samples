import os

from dotenv import load_dotenv
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import swarm

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


def market_research_team(project_description: str):
    response = str()
    try:
        perplexity_mcp_server = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="docker",
                    args=[
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "PERPLEXITY_API_KEY",
                        "mcp/perplexity-ask",
                    ],
                    env={"PERPLEXITY_API_KEY": PERPLEXITY_API_KEY},
                )
            )
        )

        with perplexity_mcp_server:
            # Initialize Strands Agent with agent_graph
            tools = perplexity_mcp_server.list_tools_sync()
            lead_market_analyst = Agent(
                system_prompt="""Conduct thorough analysis of the products and competitors, providing detailed 
                insights to guide marketing strategies. As the Lead Market Analyst at a digital marketing firm, you specialize 
                in understanding markets for new products and services. You can do web search to gather more information.
                """,
                tools=tools + [swarm],
            )

            chief_strategist = Agent(
                system_prompt="""Synthesize insights from market analysis to formulate marketing strategies. You are the Chief Strategist at a digital marketing agency,
                known for crafting custom marketing strategies that drive success of new products and services. You can do web search to gather more information.
                """,
                tools=tools,
            )

            print("\n### Market Analyst is working! ###\n")

            market_analyst_response = str(
                lead_market_analyst(
                    f"Use a swarm of 2 agents to conduct market analysis in competitive pattern. The project description is: \n\n{project_description}"
                )
            )

            print("\n### Chief Strategist is working! ###\n")

            response = str(chief_strategist(market_analyst_response))

        if len(response) > 0:
            return response

        return "I apologize, but I couldn't properly analyze your question. Could you please rephrase or provide more context?"

    # Return specific error message for English queries
    except Exception as e:
        return f"Error processing your query: {str(e)}"
