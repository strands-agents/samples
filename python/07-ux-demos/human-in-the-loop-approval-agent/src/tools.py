# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tools for the order approval agent graph."""

import uuid
from datetime import datetime, timedelta

from strands import tool, ToolContext

from data import CUSTOMERS, PRODUCT_CATALOG


@tool
def lookup_product(query: str) -> dict:
    """Search the product catalog by name or SKU.

    Args:
        query: Product name (partial match) or SKU code to search for.
    """
    query_lower = query.lower().strip()

    # Exact SKU match
    for sku, product in PRODUCT_CATALOG.items():
        if sku.lower() == query_lower:
            return {"match_type": "exact_sku", "products": [product]}

    # Substring name match
    matches = [
        p for p in PRODUCT_CATALOG.values()
        if query_lower in p["name"].lower()
    ]
    if matches:
        return {"match_type": "name_search", "products": matches}

    # No match — list available products
    available = [
        {"sku": p["sku"], "name": p["name"], "unit_price": p["unit_price"]}
        for p in PRODUCT_CATALOG.values()
    ]
    return {
        "match_type": "no_match",
        "message": f"No products found matching '{query}'.",
        "available_products": available,
    }


@tool(context=True)
def assess_order_risk(customer_name: str, order_total: float, items: list[dict], tool_context: ToolContext) -> dict:
    """Assess the risk level of an order based on customer history, order value, and inventory.

    Args:
        customer_name: The customer placing the order.
        order_total: Total dollar value of the order.
        items: List of order items, each with 'sku' and 'quantity' keys.
    """
    factors = []
    total_score = 0

    # --- Order value (0-25) ---
    if order_total > 5000:
        pts = 25
        detail = f"Order total ${order_total:,.2f} exceeds $5,000"
    elif order_total > 2000:
        pts = 20
        detail = f"Order total ${order_total:,.2f} is in the $2,000-$5,000 range"
    elif order_total > 500:
        pts = 10
        detail = f"Order total ${order_total:,.2f} is in the $500-$2,000 range"
    else:
        pts = 0
        detail = f"Order total ${order_total:,.2f} is under $500"
    factors.append({"factor": "Order value", "score": pts, "detail": detail})
    total_score += pts

    # --- Customer lookup ---
    customer = CUSTOMERS.get(customer_name.lower().strip())

    # --- New customer (0-20) ---
    if customer is None:
        pts = 20
        detail = f"Customer '{customer_name}' not found in database (new customer)"
    elif customer["account_age_months"] < 3:
        pts = 15
        detail = f"Customer account is only {customer['account_age_months']} month(s) old"
    else:
        pts = 0
        detail = f"Established customer ({customer['account_age_months']} months)"
    factors.append({"factor": "New customer", "score": pts, "detail": detail})
    total_score += pts

    # --- Customer tier (0-15) ---
    if customer is None:
        pts = 15
        detail = "Unknown customer tier"
    elif customer["tier"] == "platinum":
        pts = 0
        detail = "Platinum tier customer"
    elif customer["tier"] == "gold":
        pts = 5
        detail = "Gold tier customer"
    else:
        pts = 10
        detail = f"Standard tier customer"
    factors.append({"factor": "Customer tier", "score": pts, "detail": detail})
    total_score += pts

    # --- Payment history (0-20) ---
    if customer is None:
        pts = 10
        detail = "No payment history available"
    elif customer["payment_incidents"] >= 2:
        pts = 20
        detail = f"{customer['payment_incidents']} past payment incidents"
    elif customer["payment_incidents"] == 1:
        pts = 10
        detail = "1 past payment incident"
    else:
        pts = 0
        detail = "Clean payment history"
    factors.append({"factor": "Payment history", "score": pts, "detail": detail})
    total_score += pts

    # --- Inventory strain (0-20) ---
    inv_pts = 0
    inv_details = []
    for item in items:
        sku = item.get("sku", "")
        qty = item.get("quantity", 0)
        product = PRODUCT_CATALOG.get(sku)
        if product and product["inventory"] > 0:
            ratio = qty / product["inventory"]
            if ratio > 0.5:
                item_pts = min(int(ratio * 20), 20)
                inv_pts += item_pts
                inv_details.append(
                    f"{product['name']}: requesting {qty} of {product['inventory']} in stock ({ratio:.0%})"
                )
    inv_pts = min(inv_pts, 20)
    if inv_details:
        detail = "; ".join(inv_details)
    else:
        detail = "No inventory strain detected"
    factors.append({"factor": "Inventory strain", "score": inv_pts, "detail": detail})
    total_score += inv_pts

    # --- Risk level ---
    if total_score <= 30:
        risk_level = "low"
        recommendation = "auto_approve"
    elif total_score <= 60:
        risk_level = "medium"
        recommendation = "flag_for_review"
    else:
        risk_level = "high"
        recommendation = "flag_for_review"

    tool_context.invocation_state["risk_score"] = total_score

    return {
        "risk_score": total_score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "factors": factors,
        "customer_info": customer,
    }


@tool
def place_order(order_id: str, customer_name: str, items: list[dict]) -> dict:
    """Place an approved order: validate inventory, decrement stock, and generate confirmation.

    Args:
        order_id: The order ID (e.g., ORD-xxxx).
        customer_name: The customer name.
        items: List of items with 'sku' and 'quantity' keys.
    """
    confirmed_items = []
    failed_items = []

    for item in items:
        sku = item.get("sku", "")
        qty = item.get("quantity", 0)
        product = PRODUCT_CATALOG.get(sku)

        if not product:
            failed_items.append({"sku": sku, "reason": "Product not found"})
            continue

        if product["inventory"] < qty:
            failed_items.append({
                "sku": sku,
                "name": product["name"],
                "requested": qty,
                "available": product["inventory"],
                "reason": "Insufficient inventory",
            })
            continue

        # Decrement inventory
        product["inventory"] -= qty
        confirmed_items.append({
            "sku": sku,
            "name": product["name"],
            "quantity": qty,
            "unit_price": product["unit_price"],
            "line_total": qty * product["unit_price"],
            "remaining_inventory": product["inventory"],
        })

    # Update customer stats
    customer = CUSTOMERS.get(customer_name.lower().strip())
    if customer:
        customer["total_orders"] += 1
        customer["total_spent"] += sum(i["line_total"] for i in confirmed_items)

    order_total = sum(i["line_total"] for i in confirmed_items)
    delivery_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    confirmation_number = f"CONF-{uuid.uuid4().hex[:8].upper()}"

    return {
        "order_id": order_id,
        "confirmation_number": confirmation_number,
        "customer": customer_name,
        "confirmed_items": confirmed_items,
        "failed_items": failed_items,
        "order_total": order_total,
        "estimated_delivery": delivery_date,
        "status": "fulfilled" if not failed_items else "partially_fulfilled",
    }
