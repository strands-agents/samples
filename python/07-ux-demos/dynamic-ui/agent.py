"""A chat whose agent can render UI components in the browser."""

from datetime import date

from strands import Agent, tool

from catalog import Component
from tools import list_workouts, log_workout, summarize_workouts

SYSTEM_PROMPT = """You are a friendly assistant inside a workout log app. Today is {today}.

The app can show UI components that you choose. Prefer showing over telling: call
render_ui with the components that fit the question, for example stats for totals,
a bar_chart for trends over time, a table for a list of workouts, a form to collect
input, and buttons for useful next steps. Group related stats in a row.

Take every total, count and per-week figure from summarize_workouts. Never add up
numbers yourself.

Call render_ui first, then finish with a text reply of one or two short sentences
that appears above the components, in plain text without markdown. Don't repeat
data that is already shown in a component.

Messages that start with [ui action] come from the user clicking a button or
submitting a form you rendered, followed by the action name and the values as
JSON. Act on them (for example, log the workout), then render the updated view."""


class Chat:
    """One conversation: an agent plus the UI it rendered on the latest turn."""

    def __init__(self) -> None:
        self.ui: list[dict] = []
        self.agent = Agent(
            system_prompt=SYSTEM_PROMPT.format(today=date.today().isoformat()),
            tools=[list_workouts, summarize_workouts, log_workout, self.render_ui],
            callback_handler=None,
        )

    @tool
    def render_ui(self, components: list[Component]) -> str:
        """Show UI components to the user, in order, below your reply.

        Args:
            components: The components to show.
        """
        self.ui.extend(components)
        return "Shown to the user. Now write your short reply."

    def send(self, message: str) -> dict:
        self.ui = []
        result = self.agent(message)
        return {"text": str(result).strip(), "ui": self.ui}
