"""
Customer Profile Management for Solar KB Agent
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class CustomerProfile:
    """Customer profile data model"""

    def __init__(
        self,
        customer_id: str,
        name: str,
        email: str,
        country: str,
        state: str = None,
        purchase_history: List[Dict] = None,
        support_tickets: List[Dict] = None,
        preferences: Dict = None,
        created_at: str = None,
        updated_at: str = None,
    ):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.country = country
        self.state = state
        self.purchase_history = purchase_history or []
        self.support_tickets = support_tickets or []
        self.preferences = preferences or {}
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert profile to dictionary"""
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "country": self.country,
            "state": self.state,
            "purchase_history": self.purchase_history,
            "support_tickets": self.support_tickets,
            "preferences": self.preferences,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CustomerProfile":
        """Create profile from dictionary"""
        return cls(**data)


class CustomerProfileManager:
    """Manager for customer profiles"""

    def __init__(self, profiles_file: str = "customer_profiles.json"):
        self.profiles_file = profiles_file
        self.profiles: Dict[str, CustomerProfile] = {}
        self._load_profiles()

    def _load_profiles(self):
        """Load profiles from file"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, "r") as f:
                    profile_data = json.load(f)
                    for customer_id, data in profile_data.items():
                        self.profiles[customer_id] = CustomerProfile.from_dict(data)
            except Exception as e:
                print(f"Error loading profiles: {str(e)}")

    def _save_profiles(self):
        """Save profiles to file"""
        try:
            profile_data = {
                customer_id: profile.to_dict()
                for customer_id, profile in self.profiles.items()
            }
            with open(self.profiles_file, "w") as f:
                json.dump(profile_data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {str(e)}")

    def create_profile(self, profile_data: Dict) -> CustomerProfile:
        """Create a new customer profile"""
        if "customer_id" not in profile_data:
            profile_data["customer_id"] = str(uuid.uuid4())

        profile = CustomerProfile.from_dict(profile_data)
        self.profiles[profile.customer_id] = profile
        self._save_profiles()
        return profile

    def get_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        """Get a customer profile by ID"""
        return self.profiles.get(customer_id)

    def get_profile_by_email(self, email: str) -> Optional[CustomerProfile]:
        """Get a customer profile by email"""
        for profile in self.profiles.values():
            if profile.email.lower() == email.lower():
                return profile
        return None

    def update_profile(
        self, customer_id: str, updates: Dict
    ) -> Optional[CustomerProfile]:
        """Update a customer profile"""
        profile = self.get_profile(customer_id)
        if not profile:
            return None

        profile_dict = profile.to_dict()
        profile_dict.update(updates)
        profile_dict["updated_at"] = datetime.now().isoformat()

        updated_profile = CustomerProfile.from_dict(profile_dict)
        self.profiles[customer_id] = updated_profile
        self._save_profiles()
        return updated_profile

    def add_purchase(self, customer_id: str, purchase: Dict) -> bool:
        """Add a purchase to customer history"""
        profile = self.get_profile(customer_id)
        if not profile:
            return False

        if "purchase_id" not in purchase:
            purchase["purchase_id"] = str(uuid.uuid4())
        if "purchase_date" not in purchase:
            purchase["purchase_date"] = datetime.now().isoformat()

        profile.purchase_history.append(purchase)
        profile.updated_at = datetime.now().isoformat()
        self._save_profiles()
        return True

    def add_support_ticket(self, customer_id: str, ticket: Dict) -> bool:
        """Add a support ticket to customer history"""
        profile = self.get_profile(customer_id)
        if not profile:
            return False

        if "ticket_id" not in ticket:
            ticket["ticket_id"] = str(uuid.uuid4())
        if "created_at" not in ticket:
            ticket["created_at"] = datetime.now().isoformat()

        profile.support_tickets.append(ticket)
        profile.updated_at = datetime.now().isoformat()
        self._save_profiles()
        return True


def generate_synthetic_profiles(count: int = 10) -> List[CustomerProfile]:
    """Generate synthetic customer profiles for testing"""
    countries = ["USA", "Canada", "Australia", "UK", "Germany"]
    states = {
        "USA": ["California", "Texas", "New York", "Florida", "Washington"],
        "Canada": ["Ontario", "Quebec", "British Columbia", "Alberta"],
        "Australia": ["New South Wales", "Victoria", "Queensland"],
        "UK": ["England", "Scotland", "Wales"],
        "Germany": ["Bavaria", "Berlin", "Hesse"],
    }
    products = [
        {"name": "SolarPanel Pro", "price": 1200, "type": "panel"},
        {"name": "SolarPanel Lite", "price": 800, "type": "panel"},
        {"name": "PowerWall Battery", "price": 5000, "type": "battery"},
        {"name": "SolarInverter X1", "price": 1500, "type": "inverter"},
        {"name": "EcoCharge Controller", "price": 300, "type": "controller"},
    ]
    ticket_types = [
        "Installation",
        "Maintenance",
        "Performance",
        "Billing",
        "Technical",
    ]

    manager = CustomerProfileManager()
    created_profiles = []

    for i in range(count):
        customer_id = f"CUST{100+i}"
        name = f"Customer {i+1}"
        email = f"customer{i+1}@example.com"
        country = countries[i % len(countries)]
        state = states[country][i % len(states[country])]

        # Generate purchase history
        purchase_count = (i % 3) + 1  # 1-3 purchases
        purchases = []
        for j in range(purchase_count):
            product = products[(i + j) % len(products)]
            purchase_date = (
                datetime.now()
                .replace(month=((i + j) % 12) + 1, day=((i * j) % 28) + 1)
                .isoformat()
            )

            purchases.append(
                {
                    "purchase_id": f"PUR{100+i}{j}",
                    "product_name": product["name"],
                    "product_type": product["type"],
                    "price": product["price"],
                    "quantity": (j % 2) + 1,
                    "purchase_date": purchase_date,
                }
            )

        # Generate support tickets
        ticket_count = i % 4  # 0-3 tickets
        tickets = []
        for j in range(ticket_count):
            ticket_type = ticket_types[(i + j) % len(ticket_types)]
            created_date = (
                datetime.now()
                .replace(month=((i + j) % 12) + 1, day=((i * j) % 28) + 1)
                .isoformat()
            )

            tickets.append(
                {
                    "ticket_id": f"TKT{100+i}{j}",
                    "type": ticket_type,
                    "status": "closed" if j % 2 == 0 else "open",
                    "subject": f"{ticket_type} issue with {products[(i+j) % len(products)]['name']}",
                    "created_at": created_date,
                    "last_updated": datetime.now().isoformat(),
                }
            )

        # Generate preferences
        preferences = {
            "contact_preference": "email" if i % 2 == 0 else "phone",
            "newsletter": i % 3 == 0,
            "maintenance_reminder": i % 2 == 0,
        }

        # Create profile
        profile_data = {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "country": country,
            "state": state,
            "purchase_history": purchases,
            "support_tickets": tickets,
            "preferences": preferences,
        }

        profile = manager.create_profile(profile_data)
        created_profiles.append(profile)

    return created_profiles


if __name__ == "__main__":
    # Generate synthetic customer profiles for testing
    profiles = generate_synthetic_profiles(10)
    print(f"Generated {len(profiles)} synthetic customer profiles")
