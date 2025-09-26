"""Adapted from u03c4-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import Env
from mabench.environments.retail.data import load_data
from typing import Dict, List, Optional, Union, Any, Callable
from mabench.environments.user import UserStrategy


def browse_restaurants(
    cuisine_type: Optional[str] = None,
    location: Optional[str] = None,
    price_range: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Browse restaurants based on optional filters.

    Args:
        cuisine_type: Type of cuisine (e.g., 'italian', 'chinese', 'mexican')
        location: Location or neighborhood
        price_range: Price range indicator ('$', '$$', '$$$', '$$$$')

    Returns:
        List of matching restaurants with basic details
    """
    pass


def get_restaurant_details(restaurant_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific restaurant.

    Args:
        restaurant_id: Restaurant ID

    Returns:
        Restaurant details including hours, address, contact information, and available services
    """
    pass


def search_menu_items(
    restaurant_id: str,
    query: str = None,
    category: Optional[str] = None,
    dietary_restrictions: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Search for menu items at a restaurant.

    Args:
        restaurant_id: Restaurant ID
        query: Search term (optional)
        category: Menu category filter (e.g., 'appetizers', 'entrees', 'desserts')
        dietary_restrictions: List of dietary restrictions (e.g., 'vegetarian', 'gluten-free', 'nut-free')

    Returns:
        List of matching menu items with details and prices
    """
    pass


def get_menu_item_details(restaurant_id: str, item_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific menu item.

    Args:
        restaurant_id: Restaurant ID
        item_id: Menu item ID

    Returns:
        Menu item details including ingredients, allergens, nutritional information, and customization options
    """
    pass


def check_reservation_availability(
    restaurant_id: str, date: str, time: str, party_size: int
) -> Dict[str, Any]:
    """Check availability for a reservation.

    Args:
        restaurant_id: Restaurant ID
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        party_size: Number of people in the party

    Returns:
        Availability information including available time slots
    """
    pass


def make_reservation(
    customer_id: str,
    restaurant_id: str,
    date: str,
    time: str,
    party_size: int,
    special_requests: Optional[str] = None,
) -> Dict[str, Any]:
    """Make a reservation at a restaurant.

    Args:
        customer_id: Customer's account ID
        restaurant_id: Restaurant ID
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        party_size: Number of people in the party
        special_requests: Optional special requests for the reservation

    Returns:
        Reservation confirmation including details and confirmation number
    """
    pass


def modify_reservation(
    reservation_id: str,
    date: Optional[str] = None,
    time: Optional[str] = None,
    party_size: Optional[int] = None,
    special_requests: Optional[str] = None,
) -> Dict[str, Any]:
    """Modify an existing reservation.

    Args:
        reservation_id: Reservation ID
        date: Optional new date in YYYY-MM-DD format
        time: Optional new time in HH:MM format (24-hour)
        party_size: Optional new party size
        special_requests: Optional updated special requests

    Returns:
        Updated reservation details
    """
    pass


def cancel_reservation(reservation_id: str) -> Dict[str, str]:
    """Cancel an existing reservation.

    Args:
        reservation_id: Reservation ID

    Returns:
        Cancellation confirmation
    """
    pass


def create_order(
    customer_id: str,
    restaurant_id: str,
    items: List[Dict[str, Any]],
    delivery_address: Optional[str] = None,
    pickup_time: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new food order.

    Args:
        customer_id: Customer's account ID
        restaurant_id: Restaurant ID
        items: List of items to order, each with item_id, quantity, and customizations
        delivery_address: Optional delivery address (required for delivery orders)
        pickup_time: Optional pickup time (required for pickup orders)

    Returns:
        Order confirmation including details, total, and estimated time
    """
    pass


def add_to_order(order_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add items to an existing order that hasn't been submitted.

    Args:
        order_id: Order ID
        items: List of items to add, each with item_id, quantity, and customizations

    Returns:
        Updated order details
    """
    pass


def remove_from_order(order_id: str, item_ids: List[str]) -> Dict[str, Any]:
    """Remove items from an existing order that hasn't been submitted.

    Args:
        order_id: Order ID
        item_ids: List of item IDs to remove

    Returns:
        Updated order details
    """
    pass


def apply_coupon(order_id: str, coupon_code: str) -> Dict[str, Any]:
    """Apply a coupon to an order.

    Args:
        order_id: Order ID
        coupon_code: Coupon code to apply

    Returns:
        Updated order details with applied discount
    """
    pass


def submit_order(order_id: str, payment_method_id: str) -> Dict[str, Any]:
    """Submit an order for processing.

    Args:
        order_id: Order ID
        payment_method_id: Payment method ID to use

    Returns:
        Order submission confirmation including tracking information
    """
    pass


def track_order(order_id: str) -> Dict[str, Any]:
    """Track the status of an order.

    Args:
        order_id: Order ID

    Returns:
        Order status including current stage and estimated delivery/pickup time
    """
    pass


def get_order_history(customer_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get a customer's order history.

    Args:
        customer_id: Customer's account ID
        limit: Maximum number of orders to return (default: 5)

    Returns:
        List of past orders with basic details
    """
    pass


def get_saved_payment_methods(customer_id: str) -> List[Dict[str, Any]]:
    """Get a customer's saved payment methods.

    Args:
        customer_id: Customer's account ID

    Returns:
        List of saved payment methods with masked details
    """
    pass


def add_payment_method(
    customer_id: str, payment_details: Dict[str, str]
) -> Dict[str, Any]:
    """Add a new payment method to a customer's account.

    Args:
        customer_id: Customer's account ID
        payment_details: Payment method details including type and required information

    Returns:
        Confirmation of added payment method
    """
    pass


def get_loyalty_points(customer_id: str) -> Dict[str, Any]:
    """Get a customer's loyalty program information.

    Args:
        customer_id: Customer's account ID

    Returns:
        Loyalty program details including points balance and rewards
    """
    pass


def transfer_to_customer_service() -> Dict[str, str]:
    """Transfer the conversation to a customer service representative.

    Returns:
        Status message of the transfer
    """
    pass


ALL_TOOLS = [
    browse_restaurants,
    get_restaurant_details,
    search_menu_items,
    get_menu_item_details,
    check_reservation_availability,
    make_reservation,
    modify_reservation,
    cancel_reservation,
    create_order,
    add_to_order,
    remove_from_order,
    apply_coupon,
    submit_order,
    track_order,
    get_order_history,
    get_saved_payment_methods,
    add_payment_method,
    get_loyalty_points,
    transfer_to_customer_service,
]

WIKI = """
# Restaurant Services AI Policy

The current time is 2025-03-25 13:55:00 PST.

As a Restaurant Services AI, you can help customers browse restaurants, explore menus, make reservations, place food orders, and manage their dining experiences.

- Before taking any actions that modify a customer's account (making reservations, placing orders, adding payment methods), you must list the action details and obtain explicit customer confirmation (yes) to proceed.

- You should not provide any information, knowledge, or procedures not provided by the customer or available tools, or give subjective recommendations or comments about restaurants that could constitute personal opinions.

- You should only make one tool call at a time, and if you make a tool call, you should not respond to the customer simultaneously. If you respond to the customer, you should not make a tool call at the same time.

- You should deny customer requests that are against this policy.

- You should transfer the customer to a customer service representative if and only if the request cannot be handled within the scope of your actions or requires specialized assistance beyond your capabilities.

## Domain Basic

- Each customer has a profile containing customer ID, name, contact information, address, payment methods, dietary preferences, order history, and loyalty program information.

- Restaurants have detailed profiles including cuisine type, price range, hours, address, contact information, available services (dine-in, takeout, delivery), and menu items.

- Menu items have detailed information including description, price, ingredients, allergens, customization options, and dietary information.

- Reservations require date, time, party size, and optional special requests.

## Restaurant and Menu Information

- The assistant can help customers browse restaurants based on cuisine type, location, and price range.

- Detailed restaurant information includes hours, address, contact information, and available services.

- The assistant can search menu items based on keywords, categories, and dietary restrictions.

- Menu item details include ingredients, allergens, nutritional information, and customization options.

## Reservations

- The assistant can check reservation availability for specific dates, times, and party sizes.

- Reservation creation requires customer ID, restaurant ID, date, time, party size, and optional special requests.

- Existing reservations can be modified (date, time, party size, special requests) or canceled.

- The assistant should verify reservation details with the customer before making changes.

## Order Management

- The assistant can help customers create food orders for delivery or pickup.

- Orders require customer ID, restaurant ID, list of items (with customizations), and delivery address or pickup time.

- Items can be added to or removed from an order before submission.

- Coupons can be applied to orders to receive discounts.

- Orders are submitted with a payment method and can be tracked after submission.

## Payment and Loyalty

- The assistant can retrieve a customer's saved payment methods with masked details for security.

- New payment methods can be added to a customer's account with appropriate verification.

- The assistant can check a customer's loyalty program status including points balance and available rewards.

- Loyalty points may be applied to orders for discounts where eligible.

## Privacy and Security

- The assistant must protect customer information and only discuss account details after verification.

- Sensitive information like full credit card numbers should not be displayed in messages.

- The assistant should not ask for security credentials, PINs, or passwords under any circumstances.

- For security reasons, certain actions may require additional verification through other channels.
"""

RULES = [
    "You are a Restaurant Services AI assistant. You are chatting with a customer, and you can call tools or respond to the customer.",
    "The assistant should always first confirm the customer ID before proceeding with any account-specific task.",
    "The assistant should not proceed with any task if the customer ID is not found.",
    "For any changes to the customer's account, e.g., making reservations, placing orders, or adding payment methods, the assistant must confirm the details with the customer and ask for permission, and get explicit authorization (yes) to proceed.",
    "The assistant should solve the customer task given the tools, without transferring to customer service unless absolutely necessary.",
    "The assistant should not make up any information or knowledge about restaurants, menu items, or services not provided from the customer or the tools.",
    "The assistant should at most make one tool call at a time, and if the assistant makes a tool call, it does not respond to the customer at the same time.",
    "The assistant should never make personal recommendations or express opinions about restaurants or food items.",
    "The assistant should always clarify dietary information and allergen warnings when relevant to customer requests.",
    "The assistant should prioritize customer privacy and security, never asking for full payment details or sensitive information.",
]


class MockRestaurantEnv(Env):
    name: str = "restaurant"

    def __init__(
        self,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(
            data_load_func=load_data,
            tools=ALL_TOOLS,
            tasks=[],
            wiki=WIKI,
            rules=RULES,
            user_strategy=user_strategy,
            user_model=user_model,
            user_provider=user_provider,
            task_index=task_index,
            **kwargs,
        )
        self.terminate_tools = ["transfer_to_customer_service"]

    @property
    def tools_info(self) -> Dict[str, Dict[str, Callable]]:
        return {self.name: self.tools_map}
