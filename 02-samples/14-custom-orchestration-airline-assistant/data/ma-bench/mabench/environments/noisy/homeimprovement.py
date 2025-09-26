"""Adapted from u03c4-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import Env
from mabench.environments.retail.data import load_data
from typing import Dict, List, Optional, Union, Any, Callable
from mabench.environments.user import UserStrategy


def find_products(query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for home improvement products based on query and optional category.

    Args:
        query: Search term
        category: Optional category filter (e.g., 'flooring', 'plumbing', 'electrical')

    Returns:
        List of matching products with details and availability
    """
    pass


def get_product_details(product_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific product.

    Args:
        product_id: Product ID

    Returns:
        Product details including specifications, dimensions, price, and availability
    """
    pass


def check_product_availability(
    product_id: str, store_id: Optional[str] = None, zip_code: Optional[str] = None
) -> Dict[str, Any]:
    """Check if a product is available in a store or deliverable to a location.

    Args:
        product_id: Product ID
        store_id: Optional store ID to check in-store availability
        zip_code: Optional ZIP code to check delivery availability

    Returns:
        Availability information including stock status and delivery options
    """
    pass


def find_nearest_stores(zip_code: str) -> List[Dict[str, Any]]:
    """Find the nearest home improvement stores to a location.

    Args:
        zip_code: ZIP code to search from

    Returns:
        List of nearby stores with addresses, phone numbers, and hours
    """
    pass


def get_store_hours(store_id: str) -> Dict[str, Any]:
    """Get the operating hours for a specific store.

    Args:
        store_id: Store ID

    Returns:
        Operating hours for the store, including special holiday hours
    """
    pass


def get_installation_services(category: str) -> List[Dict[str, Any]]:
    """Get available installation services for a product category.

    Args:
        category: Product category (e.g., 'flooring', 'appliances', 'windows')

    Returns:
        List of available installation services with details and pricing
    """
    pass


def schedule_installation(
    customer_id: str,
    product_id: str,
    preferred_date: str,
    preferred_time: str,
    address: str,
) -> Dict[str, Any]:
    """Schedule an installation service for a product.

    Args:
        customer_id: Customer's account ID
        product_id: Product ID to be installed
        preferred_date: Preferred installation date in YYYY-MM-DD format
        preferred_time: Preferred time slot (e.g., 'morning', 'afternoon')
        address: Installation address

    Returns:
        Scheduled installation details including confirmation number
    """
    pass


def schedule_measurement(
    customer_id: str,
    service_type: str,
    preferred_date: str,
    preferred_time: str,
    address: str,
) -> Dict[str, Any]:
    """Schedule an in-home measurement for custom products.

    Args:
        customer_id: Customer's account ID
        service_type: Type of measurement (e.g., 'flooring', 'blinds', 'cabinets')
        preferred_date: Preferred date in YYYY-MM-DD format
        preferred_time: Preferred time slot (e.g., 'morning', 'afternoon')
        address: Measurement address

    Returns:
        Scheduled measurement details including confirmation number
    """
    pass


def schedule_consultation(
    customer_id: str,
    project_type: str,
    preferred_date: str,
    preferred_time: str,
    address: str,
) -> Dict[str, Any]:
    """Schedule an in-home consultation with a project specialist.

    Args:
        customer_id: Customer's account ID
        project_type: Type of project (e.g., 'kitchen', 'bathroom', 'deck')
        preferred_date: Preferred date in YYYY-MM-DD format
        preferred_time: Preferred time slot (e.g., 'morning', 'afternoon')
        address: Consultation address

    Returns:
        Scheduled consultation details including confirmation number
    """
    pass


def get_appointment_status(appointment_id: str) -> Dict[str, Any]:
    """Check the status of a scheduled appointment (installation, measurement, or consultation).

    Args:
        appointment_id: Appointment ID

    Returns:
        Appointment status including date, time, service type, and current status
    """
    pass


def reschedule_appointment(
    appointment_id: str, new_date: str, new_time: str
) -> Dict[str, Any]:
    """Reschedule an existing appointment.

    Args:
        appointment_id: Appointment ID
        new_date: New date in YYYY-MM-DD format
        new_time: New time slot (e.g., 'morning', 'afternoon')

    Returns:
        Updated appointment details
    """
    pass


def cancel_appointment(appointment_id: str) -> Dict[str, str]:
    """Cancel a scheduled appointment.

    Args:
        appointment_id: Appointment ID

    Returns:
        Cancellation confirmation
    """
    pass


def create_custom_order(
    customer_id: str, category: str, specifications: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a custom order for made-to-measure products.

    Args:
        customer_id: Customer's account ID
        category: Product category (e.g., 'blinds', 'cabinets', 'countertops')
        specifications: Product specifications including dimensions and materials

    Returns:
        Created custom order details including order ID and estimated completion date
    """
    pass


def get_order_status(order_id: str) -> Dict[str, Any]:
    """Check the status of an order.

    Args:
        order_id: Order ID

    Returns:
        Order status including current stage, estimated completion, and delivery details
    """
    pass


def get_warranty_information(product_id: str) -> Dict[str, Any]:
    """Get warranty information for a product.

    Args:
        product_id: Product ID

    Returns:
        Warranty details including coverage period and terms
    """
    pass


def request_quote(
    customer_id: str, service_type: str, project_details: Dict[str, Any]
) -> Dict[str, Any]:
    """Request a quote for installation or renovation services.

    Args:
        customer_id: Customer's account ID
        service_type: Type of service (e.g., 'flooring installation', 'kitchen remodel')
        project_details: Details about the project including dimensions and requirements

    Returns:
        Quote information including estimated cost and timeframe
    """
    pass


def get_diy_instructions(project_type: str) -> Dict[str, Any]:
    """Get step-by-step DIY instructions for common home improvement projects.

    Args:
        project_type: Type of DIY project (e.g., 'paint room', 'install toilet')

    Returns:
        DIY instructions including steps, tools needed, and difficulty level
    """
    pass


def add_to_shopping_list(
    customer_id: str, product_id: str, quantity: int = 1
) -> Dict[str, Any]:
    """Add a product to the customer's shopping list.

    Args:
        customer_id: Customer's account ID
        product_id: Product ID to add
        quantity: Quantity to add (default: 1)

    Returns:
        Updated shopping list information
    """
    pass


def transfer_to_specialist() -> Dict[str, str]:
    """Transfer the conversation to a home improvement specialist.

    Returns:
        Status message of the transfer
    """
    pass


ALL_TOOLS = [
    find_products,
    get_product_details,
    check_product_availability,
    find_nearest_stores,
    get_store_hours,
    get_installation_services,
    schedule_installation,
    schedule_measurement,
    schedule_consultation,
    get_appointment_status,
    reschedule_appointment,
    cancel_appointment,
    create_custom_order,
    get_order_status,
    get_warranty_information,
    request_quote,
    get_diy_instructions,
    add_to_shopping_list,
    transfer_to_specialist,
]

WIKI = """
# Home Improvement Services AI Policy

The current time is 2025-03-25 13:55:00 PST.

As a Home Improvement Services AI, you can help customers find products, schedule installations and consultations, manage appointments, request quotes, and access DIY instructions.

- Before taking any actions that modify a customer's account (scheduling appointments, creating orders, adding to shopping lists), you must list the action details and obtain explicit customer confirmation (yes) to proceed.

- You should not provide any information, knowledge, or procedures not provided by the customer or available tools, or give subjective recommendations or comments about specific products that could constitute professional advice.

- You should only make one tool call at a time, and if you make a tool call, you should not respond to the customer simultaneously. If you respond to the customer, you should not make a tool call at the same time.

- You should deny customer requests that are against this policy.

- You should transfer the customer to a home improvement specialist if and only if the request cannot be handled within the scope of your actions or requires specialized knowledge that would exceed your capabilities.

## Domain Basic

- Each customer has a profile containing customer ID, name, contact information, address, order history, and appointment history.

- Products are organized by categories (e.g., flooring, plumbing, electrical, appliances) and have detailed specifications including dimensions, materials, and installation requirements.

- Appointments can be for installation services, in-home measurements, or consultations with project specialists.

- Custom orders are available for products that require specific measurements or configurations (e.g., blinds, cabinets, countertops).

## Product Information

- The assistant can provide detailed product information including specifications, dimensions, materials, prices, and availability.

- Product availability can be checked for specific stores or for delivery to a customer's address.

- Warranty information can be provided for products, detailing coverage periods and terms.

## Installation & Services

- Installation services are available for many product categories and require scheduling an appointment.

- In-home measurements can be scheduled for products that require precise sizing (e.g., flooring, blinds, cabinets).

- Project consultations can be scheduled with specialists for more complex home improvement projects.

- All appointments require customer confirmation of date, time, and address before scheduling.

## Appointment Management

- Customers can check the status of their scheduled appointments, including installations, measurements, and consultations.

- Appointments can be rescheduled or canceled, with appropriate notice periods required for certain services.

- The assistant should verify the appointment ID before providing details or making changes.

## Custom Orders

- Custom orders can be created for products that are made-to-measure or require specific configurations.

- All custom orders require detailed specifications which may come from in-home measurements.

- Customers can check the status of their custom orders, including production stage and estimated completion date.

## DIY Support

- The assistant can provide step-by-step instructions for common DIY home improvement projects.

- DIY instructions include required tools, materials, skill level, and safety precautions.

- For complex projects, the assistant should recommend professional installation when appropriate.

## Privacy and Security

- The assistant must protect customer information and only discuss account details after verifying the customer's identity.

- Sensitive information like full credit card numbers should not be displayed in messages.

- The assistant should not ask for security credentials, PINs, or passwords under any circumstances.

- For security reasons, certain actions may require additional verification through other channels.
"""

RULES = [
    "You are a Home Improvement Services AI assistant. You are chatting with a customer, and you can call tools or respond to the customer.",
    "The assistant should always first confirm the customer ID before proceeding with any account-specific task.",
    "The assistant should not proceed with any task if the customer ID is not found.",
    "For any changes to the customer's account, e.g., scheduling appointments, creating custom orders, or adding items to shopping lists, the assistant must confirm the details with the customer and ask for permission, and get explicit authorization (yes) to proceed.",
    "The assistant should solve the customer task given the tools, without transferring to a specialist unless absolutely necessary.",
    "The assistant should not make up any information or knowledge about products, services, or installation procedures not provided from the customer or the tools.",
    "The assistant should at most make one tool call at a time, and if the assistant makes a tool call, it does not respond to the customer at the same time.",
    "The assistant should never make specific recommendations for structural modifications that could affect home safety or integrity without professional consultation.",
    "The assistant should always clarify when DIY instructions are for informational purposes only and may require professional skills or permits.",
    "The assistant should prioritize customer safety and recommend professional installation for complex or potentially dangerous projects.",
]


class MockHomeImprovementEnv(Env):
    name: str = "homeimprovement"

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
        self.terminate_tools = ["transfer_to_specialist"]

    @property
    def tools_info(self) -> Dict[str, Dict[str, Callable]]:
        return {self.name: self.tools_map}
