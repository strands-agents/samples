# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Streamlit UI for Order Approval Agent

Sidebar for order creation, main area as an order dashboard.
Uses S3 session state (multi_agent) as the source of truth for graph status.
"""

import json
import os
import uuid

import boto3
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import LayeredLayout

load_dotenv()

AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN", "")
SESSION_BUCKET = os.environ["SESSION_BUCKET"]
LOCAL_AGENT_URL = os.getenv("LOCAL_AGENT_URL", "http://localhost:8080/invocations")
LOCAL_MODE = os.getenv("LOCAL_MODE", "false").lower() == "true"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


st.set_page_config(page_title="Order Approval", page_icon="📦", layout="wide")

@st.cache_resource
def get_s3_client():
    return boto3.client("s3", region_name=AWS_REGION)

@st.cache_resource
def get_agentcore_client():
    return boto3.client("bedrock-agentcore", region_name=AWS_REGION)

def invoke_agent(payload: dict) -> dict:
    """Invoke the agent running in AgentCore Runtime."""

    if LOCAL_MODE:
        resp = requests.post(LOCAL_AGENT_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()

    runtime_session_id = payload.get("session_id", str(uuid.uuid4()))

    response = get_agentcore_client().invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=runtime_session_id,
        payload=json.dumps(payload).encode(),
    )

    chunks = []
    for chunk in response.get("response", []):
        chunks.append(chunk.decode("utf-8"))
    return json.loads("".join(chunks))

def fetch_session_state(session_id: str) -> dict | None:
    """Fetch the multi-agent session state from S3.

    The UI only reads multi_agent data, so we fetch just that file directly
    instead of listing the entire session tree.

    S3 key pattern: session_{id}/multi_agents/multi_agent_{ma_id}/multi_agent.json
    """
    multi_agent_prefix = f"session_{session_id}/multi_agents/"
    state = {"multi_agent": None}

    try:
        # Narrow list to find the multi_agent_id, then fetch directly
        response = get_s3_client().list_objects_v2(
            Bucket=SESSION_BUCKET,
            Prefix=multi_agent_prefix,
            MaxKeys=10,
        )
        for obj in response.get("Contents", []):
            if obj["Key"].endswith("/multi_agent.json"):
                body = get_s3_client().get_object(Bucket=SESSION_BUCKET, Key=obj["Key"])["Body"].read()
                state["multi_agent"] = json.loads(body)
                break

        return state
    except Exception as e:
        st.error(f"Error fetching session state: {e}")
        return None

def describe_graph() -> dict | None:
    """Fetch graph structure from the agent and cache it in session state."""
    try:
        result = invoke_agent({"action": "describe_graph"})
        if isinstance(result, str):
            result = json.loads(result)
        st.session_state["graph_def"] = result
        return result
    except Exception as e:
        st.error(f"Error fetching graph: {e}")
        return None

def get_order_status(order: dict) -> str:
    """Derive order status from the multi_agent session state."""
    multi_agent = order.get("multi_agent") or {}
    ma_status = multi_agent.get("status", "")
    if ma_status == "interrupted":
        return "pending"
    if ma_status == "completed":
        completed = set(multi_agent.get("completed_nodes", []))
        if "rejection_handler" in completed:
            return "rejected"
        return "approved"
    return "unknown"

def get_node_output(order: dict, node_id: str) -> str:
    """Extract the text output of a specific node from session state."""
    multi_agent = order.get("multi_agent") or {}
    node_results = multi_agent.get("node_results", {})
    node = node_results.get(node_id, {})
    result = node.get("result", {})
    message = result.get("message", {})
    parts = []
    for block in message.get("content", []):
        if "text" in block:
            parts.append(block["text"])
    return "\n".join(parts)

def get_status_summary(order: dict) -> str:
    """Generate a one-line summary of the current order state."""
    multi_agent = order.get("multi_agent") or {}
    ma_status = multi_agent.get("status", "")
    completed = set(multi_agent.get("completed_nodes", []))
    interrupted = set(multi_agent.get("interrupted_nodes", []))
    execution_order = multi_agent.get("execution_order", [])

    if ma_status == "interrupted":
        last_done = execution_order[-1].replace("_", " ") if execution_order else "start"
        waiting_on = next(iter(interrupted), "unknown").replace("_", " ")
        return f"Completed **{last_done}**. Waiting on **{waiting_on}** for human decision."
    if ma_status == "completed":
        if "rejection_handler" in completed:
            return "Order was **rejected** and the rejection handler has notified the customer."
        if "processor" in completed:
            if "approval_gate" not in completed:
                return "Order was **auto-approved** (low risk) and processed."
            return "Order was **approved** and processed successfully."
    return ""


def render_graph_interactive(order: dict, key_prefix: str):
    """Render the graph with clickable nodes using streamlit-flow."""
    graph_def = st.session_state.get("graph_def")
    if not graph_def:
        graph_def = describe_graph()
    if not graph_def:
        return

    node_ids = graph_def.get("nodes", [])
    edge_defs = graph_def.get("edges", [])

    multi_agent = order.get("multi_agent") or {}
    completed = set(multi_agent.get("completed_nodes", []))
    interrupted = set(multi_agent.get("interrupted_nodes", []))
    node_results = multi_agent.get("node_results", {})

    active = next(iter(interrupted), None)

    def node_style(node_id: str) -> dict:
        base = {
            "padding": "16px 28px",
            "fontSize": "16px",
            "cursor": "pointer",
            "borderRadius": "4px",
        }
        if node_id in completed:
            return {**base, "background": "#4CAF50", "color": "white", "border": "2px solid #388E3C"}
        if node_id == active:
            return {**base, "background": "#FFC107", "color": "black", "border": "2px solid #FFA000"}
        return {**base, "background": "#E0E0E0", "color": "black", "border": "2px solid #BDBDBD"}

    flow_nodes = []
    for node_id in node_ids:
        label = node_id.replace("_", " ").capitalize()
        flow_nodes.append(
            StreamlitFlowNode(
                id=node_id,
                pos=(0, 0),
                data={"content": label},
                node_type="default",
                source_position="right",
                target_position="left",
                draggable=False,
                style=node_style(node_id),
            )
        )

    flow_edges = [
        StreamlitFlowEdge(
            id=f"{e['from']}-{e['to']}",
            source=e["from"],
            target=e["to"],
            animated=False,
            marker_end={"type": "arrowclosed"},
        )
        for e in edge_defs
    ]

    flow_state_key = f"flow_state_{key_prefix}"
    selected_key = f"selected_node_{key_prefix}"

    # Store state in session_state to prevent infinite re-renders.
    # Rebuild when the order's completed/interrupted nodes change.
    order_fingerprint = (frozenset(completed), frozenset(interrupted))
    fingerprint_key = f"flow_fingerprint_{key_prefix}"

    if flow_state_key not in st.session_state or st.session_state.get(fingerprint_key) != order_fingerprint:
        st.session_state[flow_state_key] = StreamlitFlowState(flow_nodes, flow_edges)
        st.session_state[fingerprint_key] = order_fingerprint

    st.caption("Click a node to view its output details.")

    updated_state = streamlit_flow(
        key=f"flow_{key_prefix}",
        state=st.session_state[flow_state_key],
        layout=LayeredLayout(direction="right", node_layer_spacing=200, node_node_spacing=75),
        height=350,
        fit_view=True,
        show_controls=False,
        show_minimap=False,
        allow_new_edges=False,
        allow_zoom=False,
        pan_on_drag=False,
        get_node_on_click=True,
        get_edge_on_click=False,
        hide_watermark=True,
    )

    if updated_state and updated_state.selected_id:
        st.session_state[selected_key] = updated_state.selected_id

    # Show selected node details
    selected = st.session_state.get(selected_key)
    if selected and selected in node_results:
        node_data = node_results[selected]
        exec_time = node_data.get("execution_time")
        usage = node_data.get("accumulated_usage", {})

        # Metadata line
        meta_parts = []
        if exec_time:
            meta_parts.append(f"**{exec_time / 1000:.1f}s**")
        if usage.get("totalTokens"):
            meta_parts.append(f"{usage['totalTokens']} tokens")
        if meta_parts:
            st.caption(" | ".join(meta_parts))

        # Output
        output = get_node_output(order, selected)
        if output:
            with st.container(border=True):
                st.caption("OUTPUT")
                st.markdown(output)

def handle_decision(session_id: str, decision: str):
    """Send approval/rejection response back to the agent, then refresh from S3."""
    with st.spinner(f"Processing {decision}..."):
        try:
            order = st.session_state["orders"][session_id]
            interrupts = order.get("interrupts", [])
            responses = [
                {"interrupt_id": i["id"], "response": decision}
                for i in interrupts
            ]
            invoke_agent(
                {"action": "respond", "session_id": session_id, "responses": responses}
            )
            # Refresh the full state from S3
            session_state = fetch_session_state(session_id)
            if session_state and session_state.get("multi_agent") is not None:
                for key in ("display_name", "customer", "interrupts"):
                    session_state[key] = order.get(key)
                session_state["interrupts"] = []
                st.session_state["orders"][session_id] = session_state
            st.session_state["active_order"] = session_id
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------------------------------------------------------------------
# Initialize state
# ---------------------------------------------------------------------------

if "graph_def" not in st.session_state:
    describe_graph()

if "orders" not in st.session_state:
    st.session_state["orders"] = {}

all_orders = st.session_state["orders"]

# ---------------------------------------------------------------------------
# Sidebar: Create Order
# ---------------------------------------------------------------------------

SCENARIOS = {
    "Low Risk — Trusted Customer": {
        "item": "Wireless Keyboard",
        "quantity": 2,
        "customer": "Acme Corp",
        "description": "Small order from a gold-tier customer with clean history",
    },
    "Medium Risk — New Customer": {
        "item": "Noise-Cancelling Headphones",
        "quantity": 5,
        "customer": "Startup Inc",
        "description": "Moderate order from a new customer with a payment incident",
    },
    "High Risk — Unknown Customer, Large Order": {
        "item": "Motorized Standing Desk",
        "quantity": 4,
        "customer": "Unknown LLC",
        "description": "High-value order from an unknown customer, strains limited inventory",
    },
    "Inventory Strain — Bulk Furniture": {
        "item": "Standing Desk Chair",
        "quantity": 10,
        "customer": "MegaCorp LLC",
        "description": "Platinum customer but ordering most of the available stock",
    },
    "Custom Order": {
        "item": "",
        "quantity": 1,
        "customer": "",
        "description": "Enter your own order details",
    },
}

with st.sidebar:
    st.header("New Order")

    scenario_name = st.selectbox("Scenario", options=list(SCENARIOS.keys()))
    scenario = SCENARIOS[scenario_name]

    if scenario_name != "Custom Order":
        st.caption(scenario["description"])

    with st.form("order_form"):
        if scenario_name == "Custom Order":
            item_name = st.text_input("Item", placeholder="e.g., Wireless Keyboard")
            quantity = st.number_input("Qty", min_value=1, max_value=100, value=1)
            customer = st.text_input("Customer", placeholder="e.g., Acme Corp")
        else:
            item_name = st.text_input("Item", value=scenario["item"])
            quantity = st.number_input("Qty", min_value=1, max_value=100, value=scenario["quantity"])
            customer = st.text_input("Customer", value=scenario["customer"])

        submitted = st.form_submit_button("Submit Order", type="primary", use_container_width=True)

    if submitted:
        if not item_name or not customer:
            st.error("Please fill in all fields.")
        else:
            order_details = f"{quantity}x {item_name} for customer {customer}"
            session_id = str(uuid.uuid4())

            with st.spinner("Creating order..."):
                try:
                    result = invoke_agent(
                        {"action": "create", "order_details": order_details, "session_id": session_id}
                    )

                    if result.get("status") == "interrupted":
                        interrupts = result.get("interrupts", [])
                        order_state = fetch_session_state(session_id)
                        if order_state is None:
                            st.error("Order was created but failed to fetch session state from S3.")
                        else:
                            order_state["interrupts"] = interrupts
                            order_state["display_name"] = f"{quantity}x {item_name}"
                            order_state["customer"] = customer
                            st.session_state["orders"][session_id] = order_state
                            st.session_state["active_order"] = session_id
                            st.success("Order submitted!")
                            st.rerun()
                    elif result.get("status") == "completed":
                        order_state = fetch_session_state(session_id)
                        if order_state is None:
                            st.error("Order completed but failed to fetch session state from S3.")
                        else:
                            order_state["display_name"] = f"{quantity}x {item_name}"
                            order_state["customer"] = customer
                            order_state["interrupts"] = []
                            st.session_state["orders"][session_id] = order_state
                            st.session_state["active_order"] = session_id
                            st.success("Order auto-approved (low risk)!")
                            st.rerun()
                    else:
                        st.error(f"Unexpected response: {result}")
                except Exception as e:
                    st.error(f"Error: {e}")


# ---------------------------------------------------------------------------
# Main area: Order Dashboard
# ---------------------------------------------------------------------------

st.title("📦 Order Dashboard")

if not all_orders:
    st.info("No orders yet. Use the sidebar to create one.")
    st.stop()

STATUS_ORDER = {"pending": 0, "approved": 1, "rejected": 2, "unknown": 3}
sorted_orders = sorted(
    ((sid, order, get_order_status(order)) for sid, order in all_orders.items() if isinstance(order, dict)),
    key=lambda x: STATUS_ORDER.get(x[2], 99),
)

pending_count = sum(1 for _, _, s in sorted_orders if s == "pending")
processed_count = len(sorted_orders) - pending_count

current_section = None
for sid, order, status in sorted_orders:
    is_pending = status == "pending"
    section = "pending" if is_pending else "processed"

    if section != current_section:
        current_section = section
        if is_pending:
            st.subheader(f"Awaiting Approval  ({pending_count})", divider="orange")
        else:
            st.subheader(f"Completed  ({processed_count})", divider="green")

    display = order.get("display_name", sid[:8])
    customer = order.get("customer", "")

    with st.container(border=True):
        info_col, action_col = st.columns([3, 1])

        with info_col:
            if is_pending:
                st.markdown(f"**{display}**  &mdash;  {customer}")
            else:
                icon = "✅" if status == "approved" else "❌"
                st.markdown(f"{icon} **{display}**  &mdash;  {customer}")

        with action_col:
            if is_pending:
                btn_cols = st.columns(2)
                with btn_cols[0]:
                    if st.button("Approve", key=f"a_{sid}", type="primary", use_container_width=True):
                        handle_decision(sid, "approved")
                with btn_cols[1]:
                    if st.button("Reject", key=f"r_{sid}", use_container_width=True):
                        handle_decision(sid, "rejected")
            else:
                st.caption(status.upper())

        is_active = st.session_state.get("active_order") == sid
        expander_label = f"Details & Agent State — `{sid}`" if is_pending else f"Agent State — `{sid}`"
        with st.expander(expander_label, expanded=is_active):
            summary = get_status_summary(order)
            if summary:
                st.markdown(summary)
            render_graph_interactive(order, key_prefix=f"{status}-{sid}")
