#!/usr/bin/env python3

import logging


from strands import Agent
from strands_tools import file_read

from utils.prompts import JIRA_PROMPT
from utils.jira_tools import create_jira_ticket

# Enables Phoenix debug log level
logging.getLogger("phoenix").setLevel(logging.DEBUG)

# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

ticket_agent = Agent(
    system_prompt=JIRA_PROMPT,
    tools=[
        file_read,
        create_jira_ticket,
    ],
    
)


if __name__ == "__main__":
    print("\nWelcome to the Jira Ticket Assistant! 🚀")

    print(
        "This agent creates Jira tickets based on your meeting notes. It can also read from a file.\n"
    )
    query = input("\nAdd your Biweekly Sprint Meeting notes or write a .txt filename> ")
    
    ticket_agent(
        f"Use the meeting notes to create 5 Jira tickets from it: {query}"
    )
    print("\nGoodbye! 👋\n")
    print(f"\nAccumulated usage metrics:\n{ticket_agent.event_loop_metrics}")
