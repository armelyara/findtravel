"""
API wrapper functions for use in the CLI
"""
from typing import Dict, Optional, Any, List
import requests
from models.travel_plan import TravelPlan
from services.api_service import AmadeusTokenManager
from config import load_api_keys

# Initialize API clients
_api_keys = load_api_keys()
_token_manager = AmadeusTokenManager(
    _api_keys.get('amadeus_client_id', ''),
    _api_keys.get('amadeus_client_secret', '')
)

# Airline names mapping for display
AIRLINE_NAMES = {
    'AF': 'Air France',
    'DL': 'Delta Airlines',
    'BA': 'British Airways',
    'AA': 'American Airlines',
    'LH': 'Lufthansa',
    'EK': 'Emirates',
    'TK': 'Turkish Airlines',
    'ET': 'Ethiopian Airlines',
    'KQ': 'Kenya Airways',
    'RB': 'Air Afrique'
}

def search_flights(departure_iata: str, destination_iata: str, departure_date: str, 
                  return_date: str, travelers: int, max_price: float) -> Optional[Dict]:
    """
    Search flights using Amadeus API
    
    Args:
        departure_iata: Departure airport IATA code
        destination_iata: Destination airport IATA code
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD)
        travelers: Number of travelers
        max_price: Maximum price
        
    Returns:
        Flight data dictionary or None if no results
    """
    
    token = _token_manager.get_token()
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "originLocationCode": departure_iata,
        "destinationLocationCode": destination_iata,
        "departureDate": departure_date,
        "returnDate": return_date,
        "adults": travelers,
        "maxPrice": int(max_price),
        "currencyCode": "USD",
        "max": 5
    }

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error searching flights: {response.text}")
            return None
    except Exception as e:
        print(f"Network error searching flights: {e}")
        return None


def format_flight_data(flight_data: Optional[Dict], travel_plan: TravelPlan) -> str:
    """
    Format flight data with smart fallback suggestions
    
    Args:
        flight_data: Raw flight data from API
        travel_plan: Current travel plan
        
    Returns:
        Formatted flight information string
    """
    if not flight_data or 'data' not in flight_data or not flight_data['data']:
        return f"""🔍 No flights found matching your criteria.

Current search parameters:
- Departure: {travel_plan.departure['name']}
- Destination: {travel_plan.destination['name']}
- Dates: {travel_plan.departure_date} to {travel_plan.return_date}
- Budget: ${travel_plan.total_budget}
- Travelers: {travel_plan.travelers}"""

    formatted = []
    for i, option in enumerate(flight_data['data'][:3], 1):
        flight_info = f"\n{'='*50}\n[OPTION {i}]\n{'='*50}\n"
        flight_info += f"💰 Total Price: ${float(option['price']['total']):.2f}\n"

        outbound = option['itineraries'][0]
        flight_info += f"\n✈️ OUTBOUND ({outbound['duration']}):\n"
        flight_info += f"  {travel_plan.departure['name']} → {travel_plan.destination['name']}\n"
        flight_info += f"  Airline: {AIRLINE_NAMES.get(outbound['segments'][0]['carrierCode'], outbound['segments'][0]['carrierCode'])}\n"
        flight_info += f"  Stops: {len(outbound['segments'])-1}\n"

        for seg in outbound['segments']:
            flight_info += f"\n  • {seg['departure']['iataCode']} → {seg['arrival']['iataCode']}\n"
            flight_info += f"    Depart: {seg['departure']['at'][11:16]} | Arrive: {seg['arrival']['at'][11:16]}\n"
            flight_info += f"    Flight: {seg['carrierCode']}{seg['number']} | Duration: {seg.get('duration', 'N/A')}\n"

        if len(option['itineraries']) > 1:
            return_flight = option['itineraries'][1]
            flight_info += f"\n🛬 RETURN ({return_flight['duration']}):\n"
            flight_info += f"  {travel_plan.destination['name']} → {travel_plan.departure['name']}\n"
            flight_info += f"  Airline: {AIRLINE_NAMES.get(return_flight['segments'][0]['carrierCode'], return_flight['segments'][0]['carrierCode'])}\n"
            flight_info += f"  Stops: {len(return_flight['segments']) -1}\n"

            for seg in return_flight['segments']:
                flight_info += f"\n  • {seg['departure']['iataCode']} → {seg['arrival']['iataCode']}\n"
                flight_info += f"    Depart: {seg['departure']['at'][11:16]} | Arrive: {seg['arrival']['at'][11:16]}\n"
                flight_info += f"    Flight: {seg['carrierCode']}{seg['number']} | Duration: {seg.get('duration', 'N/A')}\n"

        formatted.append(flight_info)

    header = f"\n{'='*60}\n✈️ AVAILABLE FLIGHTS\n{'='*60}"
    header += f"\nFrom: {travel_plan.departure['name']} → To: {travel_plan.destination['name']}"
    header += f"\nDates: {travel_plan.departure_date} to {travel_plan.return_date}\n"

    return header + '\n'.join(formatted) + f"\n{'='*60}"

def get_hotel_suggestions(destination: str, budget: float, nights: int, travelers: int = 1) -> str:
    """
    Generate hotel suggestions based on destination and budget.
    This is a simulation function since we don't have a real hotel API.
    
    Args:
        destination: Destination city
        budget: Available budget
        nights: Number of nights
        travelers: Number of travelers
        
    Returns:
        Formatted string with hotel options
    """
    # These would normally come from an API, but we're simulating the response
    # to avoid dependency on external APIs
    price_per_night = budget / (nights * 1.5)  # Allow some budget for activities
    
    hotels = [
        {
            "name": f"{destination} Grand Hotel",
            "stars": 4,
            "area": "City Center",
            "breakfast": "Included",
            "price": price_per_night * nights * 0.9,
            "features": "Rooftop pool, spa, and central location"
        },
        {
            "name": f"{destination} Boutique Inn",
            "stars": 3,
            "area": "Historic District",
            "breakfast": "Available for purchase",
            "price": price_per_night * nights * 0.75,
            "features": "Charming historic building with local character"
        },
        {
            "name": f"Luxury Suites {destination}",
            "stars": 5,
            "area": "Marina/Waterfront",
            "breakfast": "Gourmet breakfast included",
            "price": price_per_night * nights * 1.1,
            "features": "Spacious suites with stunning views"
        }
    ]
    
    # Format hotel information
    result = ""
    for i, hotel in enumerate(hotels, 1):
        result += f"OPTION {i}: {hotel['name']} ({'⭐' * hotel['stars']})\n"
        result += f"Location: {hotel['area']}\n"
        result += f"Breakfast: {hotel['breakfast']}\n"
        result += f"Price: ${hotel['price']:.2f} total for {nights} nights\n"
        result += f"Features: {hotel['features']}\n\n"
    
    return result

def get_activity_suggestions(destination: str, budget: float, days: int) -> str:
    """
    Generate activity suggestions based on destination and budget.
    This is a simulation function since we don't have a real activity API.
    
    Args:
        destination: Destination city
        budget: Available budget
        days: Number of days
        
    Returns:
        Formatted string with activity options
    """
    # These would normally come from an API, but we're simulating the response
    daily_budget = budget / days
    
    activities = [
        {
            "name": f"{destination} City Tour",
            "cost": daily_budget * 0.2,
            "duration": "Half-day",
            "value": "Perfect introduction to the city's major landmarks",
            "category": "Cultural"
        },
        {
            "name": f"{destination} Food Experience",
            "cost": daily_budget * 0.15,
            "duration": "3 hours",
            "value": "Sample local cuisine with a knowledgeable guide",
            "category": "Culinary"
        },
        {
            "name": f"Day Trip to Surrounding Areas",
            "cost": daily_budget * 0.4,
            "duration": "Full-day",
            "value": "Explore beyond the city to see natural wonders",
            "category": "Adventure"
        },
        {
            "name": "Local Museum Pass",
            "cost": daily_budget * 0.1,
            "duration": "Flexible",
            "value": "Access to the city's top museums at your own pace",
            "category": "Cultural"
        },
        {
            "name": "Evening Entertainment",
            "cost": daily_budget * 0.25,
            "duration": "3 hours",
            "value": "Experience local performing arts or nightlife",
            "category": "Entertainment"
        }
    ]
    
    # Format activity information
    result = ""
    for i, activity in enumerate(activities, 1):
        result += f"OPTION {i}: {activity['name']}\n"
        result += f"Cost: ${activity['cost']:.2f} per person\n"
        result += f"Duration: {activity['duration']}\n"
        result += f"Why it's worth it: {activity['value']}\n"
        result += f"Category: {activity['category']}\n\n"
    
    return result