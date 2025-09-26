"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def list_all_product_types() -> str:
    """
    List the name and product id of all product types.

    Each product type has a variety of different items with unique item ids and options.
    There are only 50 product types in the store.

    Returns:
        A JSON string containing the names and product IDs of all product types.
    """
    data = load_data()
    products = data["products"]
    product_dict = {
        product["name"]: product["product_id"] for product in products.values()
    }
    product_dict = dict(sorted(product_dict.items()))
    return json.dumps(product_dict)
