# pandas_agent.py
# interacts with Pandas module wrapped in Strands @tool decorators
#

from strands import Agent
from pandas_strands_tools import pandas_tools

# Create agent with pre-loaded state and tools
agent = Agent(
    tools=pandas_tools
)

if __name__ == "__main__":
    print("Pandasbot: Ask me about spreadsheets. Type 'exit' to quit.\n")   

    response = agent("List all available pandas tools")
    print(f"\nExcelBot > {response}")

    # Run the agent in a loop for interactive conversation
    while True:
        user_input = input("\nPrompt > ")
        if user_input.lower() == "exit":
            print("Bye.")
            break
        response = agent(user_input)
        print(f"\nExcelBot > {response}")
