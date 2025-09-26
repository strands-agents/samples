"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def get_product_details(product_id: str) -> str:
    """
    Get the inventory details of a product.

    Args:
        product_id: The product id, such as '6086499569'. Be careful the product id is
                   different from the item id.

    Returns:
        A JSON string containing the product details, or an error message if not found.
    """
    data = load_data()
    products = data["products"]
    if product_id in products:
        return json.dumps(products[product_id])
    return "Error: product not found"
