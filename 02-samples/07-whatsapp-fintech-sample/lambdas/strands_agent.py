import os
import logging

from strands import Agent

from tools.cards import get_transactions, put_payment
from tools.promo import get_promotions, get_day_of_week
from utils.locales import MESSAGES


STARTUP_LOCALE=os.environ['LOCALE']
DEFAULT_MODEL=os.environ['DEFAULT_MODEL']
# Logger configuration
logger = logging.getLogger()


class StrandsAgent():
    def __init__(self):
        self.agent = Agent(
            system_prompt=MESSAGES[STARTUP_LOCALE]["system"],
            tools=[get_transactions, put_payment, get_promotions, get_day_of_week],
            model=DEFAULT_MODEL,
        )
    def get_agent_with_history(self, messages, system_prompt):
        self.agent = Agent(
            messages=messages,
            system_prompt=system_prompt,
            tools=[get_transactions, put_payment, get_promotions, get_day_of_week],
            model=DEFAULT_MODEL,
        )

    def agent_invoke(self, user_prompt, history=None):
        try:
            if history is not None:
                self.get_agent_with_history(messages=history["messages"], system_prompt=history["system_prompt"])
                result = self.agent(user_prompt)
            else:
                result = self.agent(user_prompt)
            logger.info(f"Agent result: {result}")
            return result, self.agent.messages, self.agent.system_prompt
        except Exception as e:
            logger.info(f"Error during agent invocation: {e}")
            raise