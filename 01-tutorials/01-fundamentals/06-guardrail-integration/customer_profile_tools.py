from customer_profiles import CustomerProfileManager
from strands import tool
from typing import Dict, Optional, List

# Initialize the customer profile manager
profile_manager = CustomerProfileManager()

@tool
def get_customer_profile(customer_id: str = None, email: str = None) -> Dict:
    """
    Get customer profile information by customer ID or email.
    
    Args:
        customer_id (str, optional): The customer ID to lookup
        email (str, optional): The customer email to lookup
        
    Returns:
        dict: Customer profile information or error message
    """
    if not customer_id and not email:
        return {"Either customer_id or email must be provided"}
    
    profile = None
    if customer_id:
        profile = profile_manager.get_profile(customer_id)
    elif email:
        profile = profile_manager.get_profile_by_email(email)
        
    if not profile:
        return {"Customer profile not found"}

    return profile.to_dict()


@tool
def list_customer_purchases(customer_id: str = None, email: str = None) -> List[Dict]:
    """
    Get a list of customer purchases by customer ID or email.
    
    Args:
        customer_id (str, optional): The customer ID to lookup
        email (str, optional): The customer email to lookup
        
    Returns:
        list: List of customer purchases or error message
    """
    if not customer_id and not email:
        return {"Either customer_id or email must be provided"}
    
    profile = None
    if customer_id:
        profile = profile_manager.get_profile(customer_id)

    elif email:
        profile = profile_manager.get_profile_by_email(email)
        
    if not profile:
        return {"Customer profile not found"}
        
    return profile.purchase_history


@tool
def list_customer_tickets(customer_id: str = None, email: str = None) -> List[Dict]:
    """
    Get a list of customer support tickets by customer ID or email.
    
    Args:
        customer_id (str, optional): The customer ID to lookup
        email (str, optional): The customer email to lookup
        
    Returns:
        list: List of customer support tickets or error message
    """
    if not customer_id and not email:
        return {"Either customer_id or email must be provided"}
    
    profile = None
    if customer_id:
        profile = profile_manager.get_profile(customer_id)
    elif email:
        profile = profile_manager.get_profile_by_email(email)
        
    if not profile:
        return {"Customer profile not found"}
        
    return profile.support_tickets


@tool
def update_customer_profile(customer_id: str, updates: Dict) -> Dict:
    """
    Update customer profile information.
    
    Args:
        customer_id (str): The customer ID to update
        updates (dict): The updates to apply to the profile
        
    Returns:
        dict: Updated customer profile or error message
    """
    profile = profile_manager.update_profile(customer_id, updates)
    if not profile:
        return {"Customer profile not found"}
        
    return profile.to_dict()
