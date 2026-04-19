# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Order Approval Agent - Multi-agent graph with human-in-the-loop interrupt.

Deployed to Amazon Bedrock AgentCore Runtime. Uses a Graph pattern:
  OrderCreator -> ApprovalGate (interrupt) -> OrderProcessor
"""

import json
import logging
import os
import uuid

from dotenv import load_dotenv
from strands import Agent
from strands.hooks import BeforeNodeCallEvent, HookProvider, HookRegistry
from strands.multiagent import GraphBuilder, Status
from strands.session import S3SessionManager
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import assess_order_risk, lookup_product, place_order

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# Enable debug for strands internals
logging.getLogger("strands").setLevel(logging.INFO)
logging.getLogger("strands.multiagent").setLevel(logging.INFO)

SESSION_BUCKET = os.environ["SESSION_BUCKET"]
AWS_REGION = os.environ["AWS_DEFAULT_REGION"]
MODEL_ID = os.environ["MODEL_ID"]

app = BedrockAgentCoreApp()

RISK_THRESHOLD = 30  # Orders at or below this score are auto-approved


class OrderApprovalHook(HookProvider):
    """Conditionally interrupts before the approval_gate node based on risk score."""

    def __init__(self):
        self.decision = None

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeNodeCallEvent, self.request_approval)

    def request_approval(self, event: BeforeNodeCallEvent) -> None:
        if event.node_id != "approval_gate":
            return

        risk_score = event.invocation_state.get("risk_score")
        logger.info("Risk score for approval gate: %s (threshold: %s)", risk_score, RISK_THRESHOLD)

        if risk_score is not None and risk_score <= RISK_THRESHOLD:
            logger.info("Auto-approving order (low risk)")
            self.decision = "approved"
            return

        logger.info("Requesting human approval (risk score: %s)", risk_score)
        approval = event.interrupt("order-approval", reason=f"Human approval required (risk score: {risk_score})")
        self.decision = approval.lower()


def build_graph(session_id: str):
    """Build the order approval graph with S3 session management."""
    logger.debug("Building graph with session_id=%s, bucket=%s, region=%s", session_id, SESSION_BUCKET, AWS_REGION)
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket=SESSION_BUCKET,
        region_name=AWS_REGION,
    )

    creator = Agent(
        name="creator",
        model=MODEL_ID,
        system_prompt=(
            "You are an order creation agent. When given order details, use the lookup_product tool "
            "to search the product catalog and validate that requested items exist. Use real product "
            "names, SKUs, and prices from the catalog. If a product is not found, suggest similar "
            "products from the catalog.\n\n"
            "Create a structured order summary including:\n"
            "- A unique order ID starting with 'ORD-'\n"
            "- Each line item with SKU, product name, quantity, unit price, and line total\n"
            "- The overall order total\n"
            "- Customer name\n"
            "- Inventory availability status for each item\n\n"
            "Always call lookup_product for every item mentioned in the request."
        ),
        tools=[lookup_product],
        callback_handler=None,
    )

    risk_assessor = Agent(
        name="risk_assessor",
        model=MODEL_ID,
        system_prompt=(
            "You are a risk assessment agent. Review the order details passed to you and perform "
            "a risk assessment using the assess_order_risk tool. Extract the customer name, order "
            "total, and list of items (with SKU and quantity) from the creator's output and pass "
            "them to the tool.\n\n"
            "Present the risk assessment results clearly:\n"
            "- Overall risk score and level (low/medium/high)\n"
            "- Each risk factor with its score and explanation\n"
            "- Your recommendation (approve or flag for review)\n"
            "- Summarize the order details for quick review\n\n"
            "Always call assess_order_risk exactly once."
        ),
        tools=[assess_order_risk],
        callback_handler=None,
    )

    approval_gate = Agent(
        name="approval_gate",
        model=MODEL_ID,
        system_prompt=(
            "You are an approval gate agent. Briefly summarize the order and risk assessment "
            "for the record. If the order was auto-approved (low risk), note that. If it required "
            "human review, note the decision. Keep your response concise."
        ),
        callback_handler=None,
    )

    processor = Agent(
        name="processor",
        model=MODEL_ID,
        system_prompt=(
            "You are an order processing agent. When an order has been approved, use the place_order "
            "tool to finalize the order. Extract the order ID, customer name, and item list (with "
            "SKU and quantity) from the previous agents' output.\n\n"
            "After placing the order, confirm:\n"
            "- Order ID and confirmation number\n"
            "- Items ordered with updated inventory levels\n"
            "- Estimated delivery date\n"
            "- Any items that could not be fulfilled due to inventory\n\n"
            "Always call place_order exactly once."
        ),
        tools=[place_order],
        callback_handler=None,
    )

    rejection_handler = Agent(
        name="rejection_handler",
        model=MODEL_ID,
        system_prompt=(
            "You are an order rejection handler. When an order has been rejected, acknowledge the "
            "rejection, explain that the order will not be processed, and suggest next steps the "
            "customer can take (e.g., modify the order and resubmit)."
        ),
        callback_handler=None,
    )

    approval_hook = OrderApprovalHook()

    builder = GraphBuilder()
    builder.add_node(creator, "creator")
    builder.add_node(risk_assessor, "risk_assessor")
    builder.add_node(approval_gate, "approval_gate")
    builder.add_node(processor, "processor")
    builder.add_node(rejection_handler, "rejection_handler")
    builder.add_edge("creator", "risk_assessor")
    builder.add_edge("risk_assessor", "approval_gate")
    builder.add_edge(
        "approval_gate", "processor",
        condition=lambda state: approval_hook.decision in ("approved", "y", "yes"),
    )
    builder.add_edge(
        "approval_gate", "rejection_handler",
        condition=lambda state: approval_hook.decision not in ("approved", "y", "yes"),
    )
    builder.set_entry_point("creator")
    builder.set_hook_providers([approval_hook])
    builder.set_execution_timeout(300)

    builder.set_session_manager(session_manager)

    return builder.build()

@app.entrypoint
def invoke(payload):
    """Main entrypoint for AgentCore Runtime."""
    try:
        action = payload.get("action", "create")
        session_id = payload.get("session_id") or str(uuid.uuid4())
        logger.debug("Invoke called: action=%s, session_id=%s", action, session_id)
        logger.debug("Full payload: %s", json.dumps(payload))

        graph = build_graph(session_id)

        if action == "describe_graph":
            return {
                "nodes": list(graph.nodes.keys()),
                "edges": [
                    {"from": e.from_node.node_id, "to": e.to_node.node_id}
                    for e in graph.edges
                ],
                "entry_points": [n.node_id for n in graph.entry_points],
            }
        elif action == "create":
            order_details = payload["order_details"]
            prompt = f"Create an order for: {order_details}"
            logger.debug("Creating order with prompt: %s", prompt)
            result = graph(prompt)
            logger.debug("Graph result status=%s, nodes=%s", result.status, list(result.results.keys()))

            if result.status == Status.INTERRUPTED:
                interrupts = [
                    {
                        "id": i.id,
                        "name": i.name,
                        "reason": i.reason,
                    }
                    for i in result.interrupts
                ]
                # Extract the creator's output for display
                creator_output = ""
                if "creator" in result.results and result.results["creator"].result:
                    msg = result.results["creator"].result.message
                    if msg and "content" in msg:
                        for block in msg["content"]:
                            if "text" in block:
                                creator_output += block["text"]

                return {
                    "status": result.status.value,
                    "interrupts": interrupts,
                }

            logger.debug("Order creation completed without interrupt")
            return _format_completed_result(result, session_id, graph)

        elif action == "respond":
            responses = payload["responses"]
            logger.debug("Responding to interrupts: %s", json.dumps(responses))
            interrupt_responses = [
                {"interruptResponse": {"interruptId": r["interrupt_id"], "response": r["response"]}}
                for r in responses
            ]
            logger.debug("Sending interrupt responses: %s", json.dumps(interrupt_responses))
            result = graph(interrupt_responses)
            logger.debug("Resume result status=%s, nodes=%s", result.status, list(result.results.keys()))

            if result.status == Status.INTERRUPTED:
                interrupts = [{"id": i.id, "name": i.name, "reason": i.reason} for i in result.interrupts]
                return {
                    "status": "interrupted",
                    "session_id": session_id,
                    "interrupts": interrupts,
                }

            return _format_completed_result(result, session_id, graph)

        else:
            return {"status": "error", "error": f"Unknown action: {action}"}

    except Exception as e:
        logger.exception("Error processing request")
        return {"status": "error", "error": str(e)}


def _format_completed_result(result, session_id, graph):
    """Extract text from completed graph result."""
    output_parts = []
    for node_id, node_result in result.results.items():
        if node_result.result and node_result.result.message:
            msg = node_result.result.message
            text = ""
            if "content" in msg:
                for block in msg["content"]:
                    if "text" in block:
                        text += block["text"]
            if text:
                output_parts.append({"node": node_id, "output": text})
                logger.debug("Node %s output: %s", node_id, text[:200])

    logger.debug("Formatted %d node outputs for session %s", len(output_parts), session_id)

    completed_nodes = [n.node_id for n in graph.state.completed_nodes]

    return {
        "status": "completed",
        "session_id": session_id,
        "results": output_parts,
        "completed_nodes": completed_nodes,
    }


if __name__ == "__main__":
    app.run()
