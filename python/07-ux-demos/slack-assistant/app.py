import logging
import os
import sys
import time
from typing import Any, Dict, List

from slack_bolt import App, Assistant, BoltContext, Say, SayStream, SetStatus, SetSuggestedPrompts
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.adapter.wsgi import SlackRequestHandler
from slack_sdk import WebClient
from slack_sdk.models.messages.chunk import TaskUpdateChunk
from strands import Agent, tool
from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent
from strands.models import BedrockModel
from strands.types.content import Message
from strands_tools import calculator

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


@tool
def timer(seconds: int) -> str:
    """Sleep for a specified number of seconds.

    Args:
        seconds: Number of seconds to sleep

    Returns:
        A message indicating the timer has completed
    """
    time.sleep(seconds)
    return f"Timer completed after {seconds} seconds"


app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
assistant = Assistant()
app.use(assistant)


@assistant.thread_started
def start_assistant_thread(
    say: Say,
    set_suggested_prompts: SetSuggestedPrompts,
    logger: logging.Logger,
) -> None:
    try:
        say("How can I help you?")

        prompts: List[Dict[str, str]] = [
            {"title": "Use a calculator", "message": "What is sin(0.4487)?"},
            {"title": "Set a timer", "message": "Set a timer for 5 seconds"},
        ]

        set_suggested_prompts(prompts=prompts)
    except Exception as e:
        logger.exception(f"Failed to handle thread_started: {e}")
        say(f":warning: Sorry, something went wrong during processing your request (error: {e})")


@assistant.user_message
def respond_in_assistant_thread(
    client: WebClient,
    context: BoltContext,
    logger: logging.Logger,
    say: Say,
    say_stream: SayStream,
    set_status: SetStatus,
) -> None:
    try:
        streamer = say_stream(buffer_size=32)

        set_status(
            status="Thinking…",
            loading_messages=["Pondering…", "Musing…", "Ruminating…", "Crunching…"],
        )

        if not context.channel_id or not context.thread_ts:
            say("Error: Missing channel or thread information")
            return

        replies = client.conversations_replies(
            channel=context.channel_id,
            ts=context.thread_ts,
            oldest=context.thread_ts,
            limit=10,
        )

        messages_in_thread: List[Message] = []

        for message in replies["messages"]:
            messages_in_thread.append(
                Message(
                    role="assistant" if message.get("bot_id") else "user",
                    content=[{"text": message["text"]}],
                )
            )

        def slack_callback_handler(**kwargs: Any) -> None:
            if "data" in kwargs:
                streamer.append(markdown_text=kwargs["data"])

        def track_tool_use(event: BeforeToolCallEvent) -> None:
            tool_name = event.tool_use["name"]
            tool_input = event.tool_use["input"]
            tool_use_id = event.tool_use["toolUseId"]
            streamer.append(
                chunks=[
                    TaskUpdateChunk(
                        id=tool_use_id,
                        title=f"{tool_name}",
                        details=f"```\n{tool_input}\n```",
                        status="in_progress",
                    ),
                ],
            )

        def complete_tool_use(event: AfterToolCallEvent) -> None:
            tool_name = event.tool_use["name"]
            tool_use_id = event.tool_use["toolUseId"]
            streamer.append(
                chunks=[
                    TaskUpdateChunk(
                        id=tool_use_id,
                        title=f"{tool_name}",
                        status="complete",
                    ),
                ],
            )

        slack_agent = Agent(
            model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-6"),
            system_prompt="""You are a helpful assistant. Format responses using Slack's mrkdwn:
            *bold*, _italic_, `code`, ```code blocks```, and bullet points with • or -.""",
            tools=[calculator, timer],
        )
        slack_agent.add_hook(track_tool_use, BeforeToolCallEvent)
        slack_agent.add_hook(complete_tool_use, AfterToolCallEvent)

        slack_agent(messages_in_thread, callback_handler=slack_callback_handler)
        streamer.stop()

    except Exception as e:
        logger.exception(f"Failed to respond to an inquiry: {e}")
        say(f":warning: Sorry, something went wrong during processing your request (error: {e})")


api = SlackRequestHandler(app)


def api_with_health(environ, start_response):  # type: ignore[no-untyped-def]
    if environ.get("PATH_INFO") == "/health":
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]
    return api(environ, start_response)


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
