"""Adapted from u03c4-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import Env
from mabench.environments.retail.data import load_data
from typing import Dict, List, Optional, Union, Any, Callable
from mabench.environments.user import UserStrategy


def verify_patient(
    patient_id: str = None, date_of_birth: str = None, phone: str = None
) -> Dict[str, Any]:
    """Verify a patient's identity using one or more identifiers.

    Args:
        patient_id: Patient's account ID (optional)
        date_of_birth: Patient's date of birth in YYYY-MM-DD format (optional)
        phone: Patient's phone number (optional)

    Returns:
        Patient profile including verified status and account information
    """
    pass


def find_medications(query: str) -> List[Dict[str, Any]]:
    """Search for medications based on name, generic name, or condition.

    Args:
        query: Search term (medication name, generic name, or medical condition)

    Returns:
        List of matching medications with basic information
    """
    pass


def get_medication_details(medication_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific medication.

    Args:
        medication_id: Medication ID

    Returns:
        Medication details including usage, side effects, interactions, and warnings
    """
    pass


def check_medication_interactions(medication_ids: List[str]) -> Dict[str, Any]:
    """Check for potential interactions between multiple medications.

    Args:
        medication_ids: List of medication IDs to check for interactions

    Returns:
        Interaction information including severity and recommendations
    """
    pass


def get_patient_prescriptions(patient_id: str) -> List[Dict[str, Any]]:
    """Get a list of active prescriptions for a patient.

    Args:
        patient_id: Patient's account ID

    Returns:
        List of active prescriptions with details and refill status
    """
    pass


def request_prescription_refill(
    patient_id: str, prescription_id: str, pickup_preference: str = "in-store"
) -> Dict[str, Any]:
    """Request a refill for an existing prescription.

    Args:
        patient_id: Patient's account ID
        prescription_id: Prescription ID to refill
        pickup_preference: Pickup method (in-store, drive-thru, delivery, mail)

    Returns:
        Refill request confirmation and status
    """
    pass


def transfer_prescription(
    patient_id: str, prescription_details: Dict[str, str], from_pharmacy: Dict[str, str]
) -> Dict[str, Any]:
    """Transfer a prescription from another pharmacy.

    Args:
        patient_id: Patient's account ID
        prescription_details: Details of the prescription (name, dosage, prescriber)
        from_pharmacy: Information about the source pharmacy (name, phone, address)

    Returns:
        Transfer request confirmation and next steps
    """
    pass


def check_insurance_coverage(
    patient_id: str, medication_id: str = None, insurance_id: str = None
) -> Dict[str, Any]:
    """Check insurance coverage for a patient or specific medication.

    Args:
        patient_id: Patient's account ID
        medication_id: Optional specific medication ID to check coverage
        insurance_id: Optional insurance ID if different from patient's default

    Returns:
        Insurance coverage details including copay and restrictions
    """
    pass


def update_insurance_information(
    patient_id: str, insurance_details: Dict[str, str]
) -> Dict[str, Any]:
    """Update a patient's insurance information.

    Args:
        patient_id: Patient's account ID
        insurance_details: New insurance details (provider, ID, group number, etc.)

    Returns:
        Updated insurance information confirmation
    """
    pass


def schedule_vaccination(
    patient_id: str, vaccine_type: str, preferred_date: str, preferred_time: str
) -> Dict[str, Any]:
    """Schedule a vaccination appointment.

    Args:
        patient_id: Patient's account ID
        vaccine_type: Type of vaccine (flu, covid, etc.)
        preferred_date: Preferred date in YYYY-MM-DD format
        preferred_time: Preferred time slot

    Returns:
        Scheduled vaccination details including confirmation number
    """
    pass


def check_vaccine_eligibility(patient_id: str, vaccine_type: str) -> Dict[str, Any]:
    """Check if a patient is eligible for a specific vaccine.

    Args:
        patient_id: Patient's account ID
        vaccine_type: Type of vaccine to check eligibility for

    Returns:
        Eligibility information including requirements and restrictions
    """
    pass


def find_nearest_pharmacies(zip_code: str) -> List[Dict[str, Any]]:
    """Find the nearest pharmacy locations to a ZIP code.

    Args:
        zip_code: ZIP code to search from

    Returns:
        List of nearby pharmacies with addresses, phone numbers, and hours
    """
    pass


def get_pharmacy_hours(store_id: str) -> Dict[str, Any]:
    """Get operating hours for a specific pharmacy location.

    Args:
        store_id: Pharmacy store ID

    Returns:
        Operating hours including pharmacy, drive-thru, and clinic hours
    """
    pass


def check_medication_availability(
    medication_id: str, store_id: str = None, zip_code: str = None
) -> Dict[str, Any]:
    """Check if a medication is available at a specific store or location.

    Args:
        medication_id: Medication ID
        store_id: Optional store ID to check availability
        zip_code: Optional ZIP code to check nearby stores

    Returns:
        Availability information including stock status and alternatives
    """
    pass


def find_generic_alternatives(medication_id: str) -> List[Dict[str, Any]]:
    """Find generic alternatives for a brand-name medication.

    Args:
        medication_id: Medication ID (typically a brand-name drug)

    Returns:
        List of generic alternatives with price comparisons
    """
    pass


def get_medication_price(
    medication_id: str, insurance_id: Optional[str] = None, quantity: int = 30
) -> Dict[str, Any]:
    """Get pricing information for a medication with or without insurance.

    Args:
        medication_id: Medication ID
        insurance_id: Optional insurance ID for covered pricing
        quantity: Quantity of medication (default: 30 units)

    Returns:
        Pricing information including with/without insurance and discount options
    """
    pass


def check_prescription_status(patient_id: str, prescription_id: str) -> Dict[str, Any]:
    """Check the status of a prescription or refill request.

    Args:
        patient_id: Patient's account ID
        prescription_id: Prescription ID

    Returns:
        Prescription status including processing stage and pickup availability
    """
    pass


def find_otc_products(
    query: str, category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search for over-the-counter products based on query and optional category.

    Args:
        query: Search term
        category: Optional category filter (e.g., 'pain relief', 'allergy', 'first aid')

    Returns:
        List of matching OTC products with details and availability
    """
    pass


def transfer_to_pharmacist() -> Dict[str, str]:
    """Transfer the conversation to a licensed pharmacist.

    Returns:
        Status message of the transfer
    """
    pass


ALL_TOOLS = [
    verify_patient,
    find_medications,
    get_medication_details,
    check_medication_interactions,
    get_patient_prescriptions,
    request_prescription_refill,
    transfer_prescription,
    check_insurance_coverage,
    update_insurance_information,
    schedule_vaccination,
    check_vaccine_eligibility,
    find_nearest_pharmacies,
    get_pharmacy_hours,
    check_medication_availability,
    find_generic_alternatives,
    get_medication_price,
    check_prescription_status,
    find_otc_products,
    transfer_to_pharmacist,
]

WIKI = """
# Pharmacy Services AI Policy

The current time is 2025-03-25 13:55:00 PST.

As a Pharmacy Services AI, you can help patients manage prescriptions, find medication information, check insurance coverage, schedule vaccinations, and locate pharmacy services.

- Before taking any actions that modify a patient's account (requesting refills, transferring prescriptions, updating insurance), you must list the action details and obtain explicit patient confirmation (yes) to proceed.

- You should not provide any information, knowledge, or procedures not provided by the patient or available tools, or give subjective recommendations or comments about medications that could constitute medical advice.

- You should only make one tool call at a time, and if you make a tool call, you should not respond to the patient simultaneously. If you respond to the patient, you should not make a tool call at the same time.

- You should deny patient requests that are against this policy.

- You should transfer the patient to a licensed pharmacist if and only if the request cannot be handled within the scope of your actions or requires professional pharmacy expertise beyond your capabilities.

## Domain Basic

- Each patient has a profile containing patient ID, name, date of birth, contact information, insurance information, allergies, and prescription history.

- Medications have detailed information including active ingredients, usage instructions, side effects, interactions, and contraindications.

- Prescriptions have details including medication, dosage, quantity, refills remaining, prescriber information, and fill status.

- Patient verification is required before accessing any personal health information or making account changes.

## Medication Information

- The assistant can provide general information about medications including usage, side effects, and precautions from approved sources.

- Medication interaction checks can identify potential conflicts between multiple medications.

- Generic alternatives can be suggested for brand-name medications when available.

- The assistant should always clarify that medication information is educational and not a substitute for professional medical advice.

## Prescription Management

- The assistant must verify the patient's identity before accessing or modifying prescription information.

- Prescription refill requests require patient confirmation and a valid prescription with refills remaining.

- Prescription transfers from other pharmacies require source pharmacy information and prescription details.

- The assistant can check prescription status, including processing stage and pickup availability.

## Insurance and Pricing

- Insurance coverage checks can provide information about copays and coverage limitations for medications.

- Insurance information updates require detailed new policy information and patient confirmation.

- Medication pricing can be provided with and without insurance, including discount options when available.

- The assistant should explain that pricing is estimated and may vary based on final verification.

## Vaccinations and Health Services

- Vaccination scheduling requires patient eligibility verification and confirmation of appointment details.

- The assistant can check vaccine eligibility based on patient information and vaccine requirements.

- For health consultations or clinical questions beyond general information, the assistant should refer to a pharmacist.

## Pharmacy Information

- The assistant can locate nearby pharmacies based on ZIP code and provide hours and services available.

- Medication availability can be checked at specific pharmacy locations.

- Store hours, including pharmacy, drive-thru, and clinic hours, can be provided for specific locations.

## Privacy and Security

- The assistant must adhere to healthcare privacy regulations and only discuss protected health information after patient verification.

- The assistant should not ask for or display sensitive information like full social security numbers or complete credit card numbers.

- For security reasons, certain actions may require additional verification through other channels.

- The assistant should never request password, PIN, or other security credential information.
"""

RULES = [
    "You are a Pharmacy Services AI assistant. You are chatting with a patient, and you can call tools or respond to the patient.",
    "The assistant should always first verify the patient's identity before proceeding with any health-related task.",
    "The assistant should not proceed with any task if patient verification fails.",
    "For any changes to the patient's account, e.g., requesting refills, transferring prescriptions, or updating insurance, the assistant must confirm the details with the patient and ask for permission, and get explicit authorization (yes) to proceed.",
    "The assistant should solve the patient task given the tools, without transferring to a pharmacist unless absolutely necessary.",
    "The assistant should not make up any information or knowledge about medications, health conditions, or treatments not provided from the patient or the tools.",
    "The assistant should at most make one tool call at a time, and if the assistant makes a tool call, it does not respond to the patient at the same time.",
    "The assistant should never provide medical advice, diagnose conditions, or suggest changes to prescribed medication regimens.",
    "The assistant should always clarify that medication information is educational and not a substitute for professional medical advice.",
    "The assistant should prioritize patient privacy and adhere to healthcare information protection standards.",
]


class MockPharmacyEnv(Env):
    name: str = "pharmacy"

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
        self.terminate_tools = ["transfer_to_pharmacist"]

    @property
    def tools_info(self) -> Dict[str, Dict[str, Callable]]:
        return {self.name: self.tools_map}
