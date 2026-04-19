# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""In-memory product catalog and customer database for the order approval demo."""

PRODUCT_CATALOG = {
    "KB-001": {
        "sku": "KB-001",
        "name": "Wireless Keyboard",
        "category": "Electronics",
        "unit_price": 49.99,
        "inventory": 150,
        "description": "Bluetooth mechanical keyboard with RGB backlighting",
    },
    "MN-002": {
        "sku": "MN-002",
        "name": "Ergonomic Mouse",
        "category": "Electronics",
        "unit_price": 34.99,
        "inventory": 200,
        "description": "Vertical ergonomic wireless mouse",
    },
    "CH-003": {
        "sku": "CH-003",
        "name": "Standing Desk Chair",
        "category": "Furniture",
        "unit_price": 599.99,
        "inventory": 12,
        "description": "Ergonomic mesh office chair with lumbar support",
    },
    "MG-004": {
        "sku": "MG-004",
        "name": "Company Logo Mug",
        "category": "Office Supplies",
        "unit_price": 12.99,
        "inventory": 500,
        "description": "Ceramic mug with company branding",
    },
    "LP-005": {
        "sku": "LP-005",
        "name": "Laptop Stand",
        "category": "Electronics",
        "unit_price": 79.99,
        "inventory": 45,
        "description": "Adjustable aluminum laptop stand for 13-17 inch laptops",
    },
    "HD-006": {
        "sku": "HD-006",
        "name": "Noise-Cancelling Headphones",
        "category": "Electronics",
        "unit_price": 299.99,
        "inventory": 30,
        "description": "Over-ear wireless headphones with active noise cancellation",
    },
    "WB-007": {
        "sku": "WB-007",
        "name": "Whiteboard 4x6ft",
        "category": "Office Supplies",
        "unit_price": 189.99,
        "inventory": 8,
        "description": "Magnetic dry-erase whiteboard with aluminum frame",
    },
    "DS-008": {
        "sku": "DS-008",
        "name": "Motorized Standing Desk",
        "category": "Furniture",
        "unit_price": 899.99,
        "inventory": 5,
        "description": "Electric height-adjustable standing desk, 60x30 inch",
    },
}

CUSTOMERS = {
    "acme corp": {
        "name": "Acme Corp",
        "tier": "gold",
        "total_orders": 47,
        "total_spent": 28500.00,
        "account_age_months": 24,
        "payment_incidents": 0,
    },
    "startup inc": {
        "name": "Startup Inc",
        "tier": "standard",
        "total_orders": 3,
        "total_spent": 450.00,
        "account_age_months": 2,
        "payment_incidents": 1,
    },
    "megacorp llc": {
        "name": "MegaCorp LLC",
        "tier": "platinum",
        "total_orders": 200,
        "total_spent": 150000.00,
        "account_age_months": 60,
        "payment_incidents": 0,
    },
    "globex industries": {
        "name": "Globex Industries",
        "tier": "standard",
        "total_orders": 15,
        "total_spent": 4200.00,
        "account_age_months": 8,
        "payment_incidents": 2,
    },
}
