"""
Configuration management for Travel Planner
"""
import os
from typing import Dict


def load_api_keys() -> Dict[str, str]:
    """
    Load API keys from environment variables or config file
    Returns a dictionary of API keys and credentials
    """
    
    # Load from environment variables
    keys = {
        'openai_api_key': os.environ.get('OPENAI_API_KEY'),
        'google_maps_key': os.environ.get('GOOGLE_MAPS_API_KEY'),
        'amadeus_client_id': os.environ.get('AMADEUS_CLIENT_ID'),
        'amadeus_client_secret': os.environ.get('AMADEUS_CLIENT_SECRET'),
    }
    
    # If using Google Colab, try to get from userdata
    #if any(value is None for value in keys.values()):
    #    try:
    #        from google.colab import userdata
    #        for key in keys:
    #            if keys[key] is None:
    #                try:
    #                    keys[key] = userdata.get(key.upper())
    #                except:
    #                    pass
    #    except ImportError:
    #        pass
    
    # Validate keys
    missing_keys = [k for k, v in keys.items() if v is None]
    if missing_keys:
        print(f"Warning: The following API keys are missing: {', '.join(missing_keys)}")
        print("Some features may not work without these keys.")
    
    return keys


def get_app_config() -> Dict:
    """
    Get application configuration settings
    """
    return {
        'max_flight_options': 3,
        'max_hotel_options': 3,
        'max_retries': 3,
        'cache_expiry': 1800,  # 30 minutes
        'min_budget': 100,     # Minimum budget in USD
        'default_currency': 'USD',
    }