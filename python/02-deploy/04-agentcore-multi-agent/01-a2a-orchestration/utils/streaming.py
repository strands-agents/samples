"""Streaming display utilities for Amazon Bedrock AgentCore agent responses.

Provides clean terminal output visualization for streaming agent events using
carriage return (\r) technique to overwrite status messages in-place. Creates
smooth user experience where "[Executing...]" transitions to "[Response received]"
without cluttering terminal with multiple lines per tool execution.

Key features:
- Carriage return technique for in-place status updates
- Two-layer event handling (Amazon Bedrock Converse API + Strands callbacks)
- Client-side feedback before tool results arrive
- Human-readable A2A protocol URL extraction for agent names
"""
import json


class StreamingDisplay:
    """Display streaming agent events with rich terminal visualization and hierarchy.

    Handles two layers of streaming events for comprehensive progress visualization:
    1. Amazon Bedrock Converse API events - Real-time model generation (text, tools)
    2. Strands callback events - Agent lifecycle transitions (tool results, thinking)

    Tracks tool invocation state to provide immediate client-side feedback
    ("[Executing...]") before actual tool result arrives from agent. Prevents
    perceived latency gaps during tool execution (especially for A2A calls).
    """

    def __init__(self, customer_id: str, query: str):
        """Initialize streaming display with session context.

        Args:
            customer_id: Customer identifier for display header.
            query: User query text for display header.
        """
        self.customer_id = customer_id
        self.query = query
        self.content = []
        self.current_tool = None
        self.tool_input_buffer = ""
        self.in_tool_block = False
        self.waiting_for_result = False

    def start(self):
        """Display session header with customer ID and query."""
        print(f"Customer: {self.customer_id}")
        print(f"Query: {self.query}")
        print("━" * 50)

    def handle_event(self, event: dict):
        """Process and display streaming event with appropriate formatting.

        Args:
            event: Structured event dictionary with 'type' field from orchestrator.
        """
        event_type = event.get("type")

        if event_type == "tool_start":
            self.current_tool = event.get("name")
            self.tool_input_buffer = ""
            self.in_tool_block = True
            print(f"\n> Calling {self.current_tool}")

        elif event_type == "tool_input":
            self.tool_input_buffer += event.get("input", "")

        elif event_type == "tool_complete":
            if self.in_tool_block:
                if self.tool_input_buffer:
                    try:
                        parsed = json.loads(self.tool_input_buffer)
                        # ============================================================
                        # A2A Protocol Special Handling
                        # ============================================================
                        # A2A tools use runtime URLs as identifiers. To make output
                        # human-readable, we extract agent names from URLs (e.g.,
                        # "ecommerce_order_agent" → "Order Agent"). This is purely
                        # for display - the actual A2A protocol uses full URLs.
                        if self.current_tool == "a2a_send_message":
                            msg = parsed.get("message_text", "")
                            url = parsed.get("target_agent_url", "")
                            agent_name = "Order Agent" if "order" in url.lower() else "Product Agent" if "product" in url.lower() else "Agent"
                            print(f"  ├─ To: {agent_name}")
                            print(f"  ├─ Message: {msg}")
                        elif self.current_tool == "a2a_discover_agent":
                            url = parsed.get("url", "")
                            print(f"  ├─ URL: {url}")
                        else:
                            print(f"  ├─ Input: {parsed}")
                    except json.JSONDecodeError:
                        if self.tool_input_buffer:
                            print(f"  ├─ Input: {self.tool_input_buffer}")
                print(f"  ├─ Request sent")
                # ============================================================
                # Client-Side Feedback Strategy
                # ============================================================
                # Display "[Executing...]" IMMEDIATELY after tool definition completes,
                # before waiting for actual tool result. Prevents perceived latency
                # gaps during tool execution (especially A2A calls involving network
                # round-trips to other Amazon Bedrock AgentCore runtimes). Parameters
                # end="" and flush=True keep cursor on same line for \r overwrite later.
                print(f"  └─ … Executing...", end="", flush=True)
                self.waiting_for_result = True
                self.in_tool_block = False
                self.current_tool = None
                self.tool_input_buffer = ""

        # ================================================================
        # Strands Callback Events - Agent Lifecycle During Wait Periods
        # ================================================================
        # These events fire BETWEEN Amazon Bedrock Converse API calls during
        # agent reasoning loop when processing tool results and preparing next
        # model invocation. Provide visibility into gaps after tool execution
        # completes but before model generates next response.
        elif event_type == "tool_result":
            # ============================================================
            # Carriage Return (\r) Overwrite Technique
            # ============================================================
            # Use \r to return cursor to line start, then overwrite "[Executing...]"
            # message with final result status. Creates smooth visual transition
            # without adding extra lines. Trailing spaces ensure new message fully
            # covers old one (prevents leftover characters).
            status = event.get("status", "success")
            if status == "success":
                print(f"\r  └─ Response received      ")
            else:
                print(f"\r  └─ ERROR received         ")
            self.waiting_for_result = False

        # thinking event: Fires after tool result processing, before next Amazon
        # Bedrock Converse API call. Indicates agent transitioning back to LLM for
        # continued reasoning. Occurs during "gap" between tool execution completing
        # and model generating next response, helping users understand agent lifecycle.
        elif event_type == "thinking":
            if self.waiting_for_result:
                print(f"\n  Agent thinking...")
                self.waiting_for_result = False

        elif event_type == "throttled":
            seconds = event.get("seconds", 0)
            print(f"\n  Rate limited, waiting {seconds}s...")

        elif event_type == "reasoning":
            content = event.get("content", "")[:100]
            print(f"\n  {content}...")

        elif event_type == "text":
            text = event.get("content", "")
            print(text, end="", flush=True)
            self.content.append(text)

        elif event_type == "message_stop":
            reason = event.get("reason", "")
            if reason == "end_turn":
                print("\n" + "━" * 50)
                print("Complete")

    def get_full_response(self) -> str:
        """Retrieve complete agent response text from accumulated content chunks.

        Returns:
            Concatenated response text from all text event chunks received during streaming.
        """
        return "".join(self.content)
