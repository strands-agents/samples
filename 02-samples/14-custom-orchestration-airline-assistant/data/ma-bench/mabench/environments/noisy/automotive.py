"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import Env
from mabench.environments.retail.data import load_data
from typing import Dict, List, Optional, Union, Any, Callable
from mabench.environments.user import UserStrategy


def search_vehicle_parts(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for vehicle parts by name, brand, or compatibility.

    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 10)

    Returns:
        List of part objects with id, name, brand, compatibility, and price
    """
    pass


def get_part_details(part_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific vehicle part.

    Args:
        part_id: Vehicle part ID

    Returns:
        Part details including specifications and compatibility
    """
    pass


def create_maintenance_plan(
    vehicle_id: str, name: str, description: str
) -> Dict[str, Any]:
    """Create a new maintenance plan for a vehicle.

    Args:
        vehicle_id: Vehicle's ID
        name: Name of the maintenance plan
        description: Description of the maintenance plan

    Returns:
        Details of the created maintenance plan including ID
    """
    pass


def add_services_to_plan(plan_id: str, service_ids: List[str]) -> Dict[str, Any]:
    """Add services to an existing maintenance plan.

    Args:
        plan_id: Maintenance plan ID
        service_ids: List of service IDs to add

    Returns:
        Status of the operation
    """
    pass


def get_customer_vehicles(customer_id: str) -> List[Dict[str, Any]]:
    """Get a list of the customer's registered vehicles.

    Args:
        customer_id: Customer's ID

    Returns:
        List of vehicle objects with id, make, model, and year
    """
    pass


def get_maintenance_history(vehicle_id: str) -> List[Dict[str, Any]]:
    """Get the maintenance history for a vehicle.

    Args:
        vehicle_id: Vehicle ID

    Returns:
        List of service records for the vehicle
    """
    pass


def get_service_recommendations(vehicle_id: str, mileage: int) -> List[Dict[str, Any]]:
    """Get service recommendations based on vehicle and mileage.

    Args:
        vehicle_id: Vehicle ID
        mileage: Current mileage of the vehicle

    Returns:
        List of recommended service objects
    """
    pass


def schedule_maintenance_appointment(
    vehicle_id: str, service_ids: List[str], preferred_date: str
) -> Dict[str, Any]:
    """Schedule a maintenance appointment for a vehicle.

    Args:
        vehicle_id: Vehicle ID
        service_ids: List of service IDs to be performed
        preferred_date: Preferred appointment date (YYYY-MM-DD)

    Returns:
        Appointment details including confirmation number
    """
    pass


def get_customer_profile(customer_id: str) -> Dict[str, Any]:
    """Get a customer's profile information.

    Args:
        customer_id: Customer's ID

    Returns:
        Customer profile details including contact information and membership level
    """
    pass


def get_customer_appointments(
    customer_id: str, status: str = "all"
) -> List[Dict[str, Any]]:
    """Get a customer's appointments.

    Args:
        customer_id: Customer's ID
        status: Filter by status (all, upcoming, completed, canceled)

    Returns:
        List of the customer's appointment records
    """
    pass


def check_appointment_availability(location_id: str, date: str) -> Dict[str, Any]:
    """Check available appointment slots for a specific date and location.

    Args:
        location_id: ID of the service center location
        date: Date to check (YYYY-MM-DD)

    Returns:
        Available time slots for the specified date
    """
    pass


def update_appointment(
    appointment_id: str,
    new_date: Optional[str] = None,
    new_services: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Update an existing appointment.

    Args:
        appointment_id: ID of the appointment to update
        new_date: New appointment date (YYYY-MM-DD) if changing date
        new_services: New list of service IDs if changing services

    Returns:
        Updated appointment details
    """
    pass


def cancel_appointment(appointment_id: str) -> Dict[str, Any]:
    """Cancel an existing appointment.

    Args:
        appointment_id: ID of the appointment to cancel

    Returns:
        Status of the cancellation operation
    """
    pass


def get_service_centers(zip_code: str, radius: int = 25) -> List[Dict[str, Any]]:
    """Find service centers near a location.

    Args:
        zip_code: ZIP code to search near
        radius: Search radius in miles (default: 25)

    Returns:
        List of service centers with their details and distance
    """
    pass


def register_new_vehicle(
    customer_id: str, make: str, model: str, year: int, vin: str
) -> Dict[str, Any]:
    """Register a new vehicle for a customer.

    Args:
        customer_id: Customer's ID
        make: Vehicle make
        model: Vehicle model
        year: Vehicle year
        vin: Vehicle Identification Number

    Returns:
        Created vehicle details
    """
    pass


def check_recall_info(vin: str) -> List[Dict[str, Any]]:
    """Check for recall information on a vehicle.

    Args:
        vin: Vehicle Identification Number

    Returns:
        List of active recalls for the vehicle
    """
    pass


def calculate_service_cost(service_ids: List[str], vehicle_id: str) -> Dict[str, Any]:
    """Calculate the cost of selected services for a vehicle.

    Args:
        service_ids: List of service IDs
        vehicle_id: Vehicle ID

    Returns:
        Detailed cost breakdown including parts, labor, and total
    """
    pass


def fetch_service_catalog(vehicle_id: str) -> List[Dict[str, Any]]:
    """Get the catalog of available services for a specific vehicle.

    Args:
        vehicle_id: Vehicle ID

    Returns:
        List of available services with descriptions and base prices
    """
    pass


def enroll_in_service_membership(customer_id: str, plan_type: str) -> Dict[str, Any]:
    """Enroll a customer in a service membership plan.

    Args:
        customer_id: Customer's ID
        plan_type: Type of membership plan (basic, premium, or elite)

    Returns:
        Membership details including benefits and expiration
    """
    pass


def transfer_to_human_technician() -> Dict[str, str]:
    """Transfer the conversation to a human automotive technician.

    Returns:
        Status message of the transfer
    """
    pass


ALL_TOOLS = [
    search_vehicle_parts,
    get_part_details,
    create_maintenance_plan,
    add_services_to_plan,
    get_customer_vehicles,
    get_maintenance_history,
    get_service_recommendations,
    schedule_maintenance_appointment,
    get_customer_profile,
    get_customer_appointments,
    check_appointment_availability,
    update_appointment,
    cancel_appointment,
    get_service_centers,
    register_new_vehicle,
    check_recall_info,
    calculate_service_cost,
    fetch_service_catalog,
    enroll_in_service_membership,
    transfer_to_human_technician,
]

WIKI = """
# Automotive Service AI Policy

The current time is 2025-03-25 11:35:00 PST.

As an Automotive Service AI, you can help customers manage vehicle maintenance, schedule service appointments, and explore service options for their vehicles.

- Before taking any actions that modify a customer's account (scheduling appointments, registering vehicles, enrolling in memberships), you must list the action details and obtain explicit user confirmation (yes) to proceed.

- You should not provide any information, knowledge, or procedures not provided by the user or available tools, or give subjective recommendations about vehicle quality or unauthorized repairs.

- You should only make one tool call at a time, and if you make a tool call, you should not respond to the user simultaneously. If you respond to the user, you should not make a tool call at the same time.

- You should deny user requests that are against this policy.

- You should transfer the user to a human technician specialist if and only if the request cannot be handled within the scope of your actions.

## Domain Basic

- Each customer has a profile containing customer ID, name, contact information, membership level (None, Basic, Premium, or Elite), registered vehicles, and appointment history.

- Each vehicle has a vehicle ID, make, model, year, VIN, and maintenance history.

- Each service has a service ID, name, description, estimated duration, and base price (which may vary by vehicle).

- Each appointment has an appointment ID, vehicle ID, scheduled date and time, service center location, selected services, estimated cost, and status (scheduled, completed, or canceled).

## Service Recommendations

- The AI must first confirm the customer's ID and vehicle information before proceeding with personalized recommendations.

- Recommendations can be generated based on vehicle make, model, year, mileage, and maintenance history using the get_service_recommendations function.

- The AI should explain the importance of recommended maintenance items but should not exaggerate risks or consequences.

- Maintenance plans can be created for regular service schedules using create_maintenance_plan and add_services_to_plan.

## Appointment Scheduling

- Scheduling appointments: The AI can check availability at nearby service centers and schedule appointments for specific dates and times.

- Before scheduling, the AI should confirm the vehicle, services, location, and time with the customer.

- Appointments can be updated or canceled up to 24 hours before the scheduled time without any fee.

- Premium and Elite members have priority scheduling and can book appointments with shorter notice.

## Vehicle Management

- The AI can help customers register new vehicles to their account using register_new_vehicle.

- Vehicle maintenance history can be accessed to provide service records and track maintenance intervals.

- Recall information can be checked using the vehicle's VIN to ensure safety compliance.

- The AI should recommend maintenance based on manufacturer guidelines and the vehicle's specific maintenance schedule.

## Service Pricing and Membership

- The AI can calculate service costs based on the selected services, vehicle type, and applicable membership discounts.

- Membership benefits: Basic includes 10% off services, Premium includes 15% off services and free oil changes, Elite includes 20% off services, free oil changes, and priority scheduling.

- Cost estimates provided by the AI are subject to change upon actual inspection of the vehicle.

- The AI should clearly explain any membership enrollment terms, including annual fees and cancellation policies.

## Feature Limitations

- Some advanced diagnostics and specialized repairs may require in-person inspection and cannot be accurately assessed by the AI.

- Service availability may vary by location and vehicle type. The AI should inform customers when a requested service is not available for their vehicle or at their preferred location.

- Emergency roadside assistance requests should be directed to the emergency services number rather than scheduled through the AI.

## Privacy and Consent

- The AI must respect customers' privacy and obtain consent before accessing their vehicle history or scheduling appointments.

- The AI should not share a customer's personal information or vehicle details with unauthorized parties.

- For any personalized recommendation that requires accessing the customer's vehicle data, the AI should explain what data will be used and get customer consent.
"""

RULES = [
    "You are an Automotive Service AI assistant. You are chatting with a customer, and you can call tools or respond to the customer.",
    "The AI should always first confirm the customer ID and vehicle information before proceeding with any personalized task.",
    "The AI should not proceed with any task if the customer ID or vehicle information is not found.",
    "For any changes to the customer's account, e.g., appointment scheduling, vehicle registration, or membership enrollment, the AI must confirm the details with the customer and ask for permission, and get explicit authorization (yes) to proceed.",
    "The AI should solve the customer task given the tools, without transferring to a human technician unless absolutely necessary.",
    "The AI should not make up any information or knowledge about vehicles, services, or features not provided from the user or the tools.",
    "The AI should at most make one tool call at a time, and if the AI makes a tool call, it does not respond to the user at the same time.",
    "The AI should respect membership limitations and inform non-members when a membership feature is requested.",
    "The AI should not provide any subjective opinions on vehicle quality or unauthorized repair procedures.",
    "The AI should prioritize customer privacy and only access vehicle history with consent.",
]


class MockAutomotiveDomainEnv(Env):
    name: str = "automotive"

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
        self.terminate_tools = ["transfer_to_human_technician"]

    @property
    def tools_info(self) -> Dict[str, Dict[str, Callable]]:
        return {self.name: self.tools_map}
