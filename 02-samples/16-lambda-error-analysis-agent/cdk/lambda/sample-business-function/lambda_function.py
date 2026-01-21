import json
import os
import boto3
from datetime import datetime
from decimal import Decimal
from aws_lambda_powertools import Logger

# Import decorator
from decorator import error_capture

# Setup
logger = Logger()
eventbridge = boto3.client('events')
event_bus_name = os.environ.get('EVENT_BUS_NAME')

@error_capture(
    logger=logger,
    eventbridge_client=eventbridge,
    event_bus_name=event_bus_name,
    publish_succeeded=True,
    publish_failed_on_error=True,
    publish_failed_on_exception=True,
    expose_errors=True
)
def lambda_handler(event, context):
    """
    User Data Enrichment Lambda
    Processes user registration data, validates, enriches, and formats for downstream systems
    """
    
    # Extract user data from event
    user_data = event.get('user_data', {})
    logger.info(f"Processing user registration for: {user_data.get('email')}")
    
    # Validate and enrich user data
    enriched_user = enrich_user_profile(user_data)
    
    # Calculate user tier and benefits
    user_tier = calculate_user_tier(enriched_user)
    
    # Format response
    response_data = format_user_response(enriched_user, user_tier)
    
    return {
        "statusCode": 200,
        "info": f"User profile processed successfully",
        "data": response_data
    }

def enrich_user_profile(user_data):
    """
    Enrich user profile with derived fields and validation
    Extracts, validates, and transforms user registration data
    """
    
    # Extract and normalize email
    email = user_data['email'].lower().strip()
    
    # Parse full name into components
    full_name = user_data['profile']['name']
    name_parts = full_name.split(' ')
    first_name = name_parts[0]
    last_name = name_parts[-1]
    
    # Validate and convert age
    age = int(user_data.get('age', 0))
    
    # Calculate account balance with signup bonus
    account_balance = Decimal(str(user_data.get('initial_deposit', 0)))
    bonus = account_balance * Decimal('0.1')  # 10% signup bonus
    total_balance = float(account_balance + bonus)
    
    # Parse registration date
    registration_date = datetime.strptime(
        user_data['registration_date'], 
        '%Y-%m-%d'
    )
    
    # Extract notification preferences
    preferences = user_data['settings']['preferences']['notifications']
    
    return {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'age': age,
        'balance': total_balance,
        'registration_date': registration_date.isoformat(),
        'preferences': preferences
    }

def calculate_user_tier(user_profile):
    """
    Calculate user tier based on profile data
    Determines membership level using balance and engagement metrics
    """
    
    balance = user_profile['balance']
    age = user_profile['age']
    
    # Calculate balance per year of age (engagement metric)
    balance_per_year = balance / age
    
    # Count active notification preferences
    notification_count = len(user_profile['preferences'])
    
    # Calculate tier score
    tier_score = (balance_per_year * 0.7) + (notification_count * 0.3)
    
    if tier_score > 1000:
        return 'platinum'
    elif tier_score > 500:
        return 'gold'
    elif tier_score > 100:
        return 'silver'
    else:
        return 'bronze'

def format_user_response(user_profile, tier):
    """Format final response for downstream systems"""
    return {
        'user': {
            'email': user_profile['email'],
            'name': f"{user_profile['first_name']} {user_profile['last_name']}",
            'tier': tier
        },
        'account': {
            'balance': user_profile['balance'],
            'registration_date': user_profile['registration_date']
        },
        'processed_at': datetime.utcnow().isoformat()
    }