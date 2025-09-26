"""Adapted from u03c4-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import Env
from mabench.environments.retail.data import load_data
from typing import Dict, List, Optional, Union, Any, Callable
from mabench.environments.user import UserStrategy


def verify_customer(
    customer_id: str = None, email: str = None, phone: str = None
) -> Dict[str, Any]:
    """Verify a customer's identity using one or more identifiers.

    Args:
        customer_id: Customer's account ID (optional)
        email: Customer's email address (optional)
        phone: Customer's phone number (optional)

    Returns:
        Customer profile including verified status and account information
    """
    pass


def get_customer_products(customer_id: str) -> List[Dict[str, Any]]:
    """Get a list of products owned by the customer.

    Args:
        customer_id: Customer's account ID

    Returns:
        List of products with product ID, name, purchase date, and warranty status
    """
    pass


def get_product_details(product_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific product.

    Args:
        product_id: Product ID

    Returns:
        Product details including specifications, warranty information, and support history
    """
    pass


def search_knowledge_base(
    query: str, product_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search the knowledge base for articles related to the query.

    Args:
        query: Search query
        product_id: Optional product ID to filter results

    Returns:
        List of knowledge base articles with titles and summaries
    """
    pass


def get_article_content(article_id: str) -> Dict[str, Any]:
    """Get the full content of a knowledge base article.

    Args:
        article_id: Knowledge base article ID

    Returns:
        Full article content with title, body, and related topics
    """
    pass


def create_support_ticket(
    customer_id: str, product_id: str, issue_description: str, priority: str = "medium"
) -> Dict[str, Any]:
    """Create a new support ticket for a customer issue.

    Args:
        customer_id: Customer's account ID
        product_id: Product ID
        issue_description: Description of the issue
        priority: Priority level (low, medium, high, critical)

    Returns:
        Created ticket details including ticket ID and estimated response time
    """
    pass


def get_ticket_status(ticket_id: str) -> Dict[str, Any]:
    """Get the status of a support ticket.

    Args:
        ticket_id: Support ticket ID

    Returns:
        Ticket status including current state, assigned agent, and updates
    """
    pass


def update_ticket(
    ticket_id: str, comment: str, status: Optional[str] = None
) -> Dict[str, Any]:
    """Add a comment to a ticket and optionally update its status.

    Args:
        ticket_id: Support ticket ID
        comment: Comment to add to the ticket
        status: Optional new status (open, in_progress, on_hold, resolved, closed)

    Returns:
        Updated ticket details
    """
    pass


def run_diagnostics(product_id: str, diagnostic_type: str) -> Dict[str, Any]:
    """Run diagnostics on a product to identify issues.

    Args:
        product_id: Product ID
        diagnostic_type: Type of diagnostic to run (basic, advanced, network, hardware, software)

    Returns:
        Diagnostic results including identified issues and recommendations
    """
    pass


def get_troubleshooting_steps(issue_id: str) -> List[Dict[str, Any]]:
    """Get step-by-step troubleshooting instructions for a known issue.

    Args:
        issue_id: Issue identifier

    Returns:
        List of troubleshooting steps in sequential order
    """
    pass


def check_warranty_status(product_id: str) -> Dict[str, Any]:
    """Check the warranty status of a product.

    Args:
        product_id: Product ID

    Returns:
        Warranty details including expiration date, coverage type, and eligibility for service
    """
    pass


def schedule_repair(
    customer_id: str, product_id: str, preferred_date: str, issue_description: str
) -> Dict[str, Any]:
    """Schedule a repair service for a product.

    Args:
        customer_id: Customer's account ID
        product_id: Product ID
        preferred_date: Preferred service date in YYYY-MM-DD format
        issue_description: Description of the issue

    Returns:
        Scheduled repair details including confirmation number and time window
    """
    pass


def initiate_return(customer_id: str, product_id: str, reason: str) -> Dict[str, Any]:
    """Initiate a return process for a product.

    Args:
        customer_id: Customer's account ID
        product_id: Product ID
        reason: Reason for return

    Returns:
        Return details including return authorization number and instructions
    """
    pass


def check_order_status(order_id: str) -> Dict[str, Any]:
    """Check the status of an order.

    Args:
        order_id: Order ID

    Returns:
        Order status including current state, shipping information, and estimated delivery
    """
    pass


def generate_return_label(return_id: str) -> Dict[str, Any]:
    """Generate a return shipping label for an authorized return.

    Args:
        return_id: Return authorization ID

    Returns:
        Return label details including tracking number and download link
    """
    pass


def get_software_updates(product_id: str) -> List[Dict[str, Any]]:
    """Get available software updates for a product.

    Args:
        product_id: Product ID

    Returns:
        List of available updates with version numbers, release dates, and change logs
    """
    pass


def check_service_outages(
    service_id: Optional[str] = None, zip_code: Optional[str] = None
) -> Dict[str, Any]:
    """Check for service outages in a specific area or for a specific service.

    Args:
        service_id: Optional service identifier
        zip_code: Optional ZIP code to check for location-specific outages

    Returns:
        Service outage information including affected areas and estimated resolution time
    """
    pass


def get_nearest_service_centers(zip_code: str) -> List[Dict[str, Any]]:
    """Find the nearest service centers to a location.

    Args:
        zip_code: ZIP code to search from

    Returns:
        List of service centers with addresses, hours, and available services
    """
    pass


def transfer_to_human_agent(department: str = "general") -> Dict[str, str]:
    """Transfer the conversation to a human support agent.

    Args:
        department: Department to transfer to (general, technical, billing, warranty)

    Returns:
        Status message of the transfer
    """
    pass


ALL_TOOLS = [
    verify_customer,
    get_customer_products,
    get_product_details,
    search_knowledge_base,
    get_article_content,
    create_support_ticket,
    get_ticket_status,
    update_ticket,
    run_diagnostics,
    get_troubleshooting_steps,
    check_warranty_status,
    schedule_repair,
    initiate_return,
    check_order_status,
    generate_return_label,
    get_software_updates,
    check_service_outages,
    get_nearest_service_centers,
    transfer_to_human_agent,
]

WIKI = """
# Tech Support AI Policy

The current time is 2025-03-24 23:00:00 PST.

As a Tech Support AI, you can help users troubleshoot technical issues, manage support tickets, check warranty status, and schedule repairs for their products.

- Before taking any actions that modify a user's account (creating tickets, scheduling repairs, initiating returns), you must list the action details and obtain explicit user confirmation (yes) to proceed.

- You should not provide any information, knowledge, or procedures not provided by the user or available tools, or give subjective recommendations or comments about products outside of technical support context.

- You should only make one tool call at a time, and if you make a tool call, you should not respond to the user simultaneously. If you respond to the user, you should not make a tool call at the same time.

- You should deny user requests that are against this policy.

- You should transfer the user to a human agent if and only if the request cannot be handled within the scope of your actions or requires specialized technical expertise beyond your capabilities.

## Domain Basic

- Each customer has a profile containing customer ID, name, contact information, address, purchase history, and owned products.

- Each product has a product ID, name, model number, purchase date, warranty information, and support history.

- Support tickets have a ticket ID, creation date, product ID, issue description, priority level, status, and comment history.

- Knowledge base articles contain structured troubleshooting steps, known issues, and solutions for specific products and problem types.

## Customer Verification

- The support agent must first verify the customer's identity before providing account-specific information or taking actions on their behalf.

- Verification can be done using customer ID, registered email address, or phone number.

- The agent should not proceed with any customer-specific task if verification fails.

## Issue Diagnosis

- The agent should work to understand the issue through diagnostic questions before recommending solutions.

- Diagnostic tools can be run on compatible products to automatically identify hardware, software, or network issues.

- The agent should check if the issue is related to a known problem with available troubleshooting steps.

- For complex issues, the agent should create a support ticket with detailed information about the problem and steps already attempted.

## Troubleshooting

- The agent can provide step-by-step instructions to resolve common issues using the knowledge base.

- Troubleshooting steps should be presented in a clear, sequential order and confirmed with the user after each step.

- If basic troubleshooting fails, the agent should escalate to more advanced diagnostics or recommend creating a support ticket.

- For software issues, the agent should check if software updates are available that might resolve the problem.

## Service and Warranty

- The agent can check warranty status for products and explain coverage details.

- For products under warranty, the agent can schedule repairs or replacements according to the warranty terms.

- For out-of-warranty products, the agent should provide service options with associated costs.

- The agent can help initiate returns for eligible products and generate return shipping labels.

## Service Status

- The agent can check the status of existing support tickets, orders, and repair services.

- For service outages, the agent can provide information about affected areas, services, and estimated resolution times.

- The agent can locate the nearest service centers based on the customer's location for in-person assistance.

## Privacy and Security

- The agent must protect customer information and only discuss account details after verification.

- The agent should not ask for security credentials, PINs, or passwords under any circumstances.

- Sensitive information like full credit card numbers should never be requested or displayed in messages.

- For security reasons, certain actions may require additional verification through other channels.
"""

RULES = [
    "You are a Tech Support AI assistant. You are chatting with a customer, and you can call tools or respond to the user.",
    "The agent should always first verify the customer's identity before proceeding with any account-specific task.",
    "The agent should not proceed with any task if customer verification fails.",
    "For any changes to the customer's account, e.g., creating tickets, scheduling repairs, or initiating returns, the agent must confirm the details with the user and ask for permission, and get explicit authorization (yes) to proceed.",
    "The agent should solve the user task given the tools, without transferring to a human agent unless absolutely necessary.",
    "The agent should not make up any information or knowledge about products, troubleshooting steps, or technical specifications not provided from the user or the tools.",
    "The agent should at most make one tool call at a time, and if the agent makes a tool call, it does not respond to the user at the same time.",
    "The agent should present troubleshooting steps in a clear, sequential manner and confirm completion at each stage.",
    "The agent should prioritize customer privacy and security, never asking for credentials or sensitive account details.",
    "The agent should acknowledge the limitations of remote troubleshooting and recommend in-person service when appropriate.",
]


class MockTechSupportEnv(Env):
    name: str = "techsupport"

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
        self.terminate_tools = ["transfer_to_human_agent"]

    @property
    def tools_info(self) -> Dict[str, Dict[str, Callable]]:
        return {self.name: self.tools_map}
