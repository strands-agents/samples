from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from agent import ConversionAgent


class ConversionAgentExecutor(AgentExecutor):
    """Mathematical Conversion AgentExecutor."""

    def __init__(self):
        self.agent = ConversionAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        result = self.agent.invoke(query, context.context_id)

        content = result["content"]

        event_queue.enqueue_event(new_agent_text_message(content))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
