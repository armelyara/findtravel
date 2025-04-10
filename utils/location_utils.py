"""
Utility functions for location search, validation, and manipulation
used throughout the travel planner application.
"""

import re
from difflib import get_close_matches
import json
import os

# Sample data structures for storing location information
# In a production app, this would likely be replaced with a database or API
class LocationData:
    def __init__(self, data_file=None):
        """
        Initialize location data from a file or use default data.
        
        Args:
            data_file (str, optional): Path to JSON file with location data
        """
        self._cities = {}
        self._airports = {}
        self._countries = {}
        
        if data_file and os.path.exists(data_file):
            self._load_from_file(data_file)
        else:
            # Default minimal dataset if no file is provided
            self._init_default_data()
    
    def _load_from_file(self, data_file):
        """Load location data from a JSON file."""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cities = data.get('cities', {})
                self._airports = data.get('airports', {})
                self._countries = data.get('countries', {})
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading location data: {e}")
            self._init_default_data()
    
    def _init_default_data(self):
        """Initialize with a minimal default dataset."""
        # Sample data - in a real application, this would be much more comprehensive
        self._countries = {
            "US": {"name": "United States", "code": "US", "continent": "North America"},
            "UK": {"name": "United Kingdom", "code": "UK", "continent": "Europe"},
            "FR": {"name": "France", "code": "FR", "continent": "Europe"},
            "JP": {"name": "Japan", "code": "JP", "continent": "Asia"},
            "AU": {"name": "Australia", "code": "AU", "continent": "Oceania"}
        }
        
        self._cities = {
            "new york": {"name": "New York", "country": "US", "population": 8804190},
            "los angeles": {"name": "Los Angeles", "country": "US", "population": 3898747},
            "london": {"name": "London", "country": "UK", "population": 8982000},
            "paris": {"name": "Paris", "country": "FR", "population": 2161000},
            "tokyo": {"name": "Tokyo", "country": "JP", "population": 13960000},
            "sydney": {"name": "Sydney", "country": "AU", "population": 5312000}
        }
        
        self._airports = {
            "JFK": {"name": "John F. Kennedy International Airport", "city": "new york", "iata": "JFK"},
            "LAX": {"name": "Los Angeles International Airport", "city": "los angeles", "iata": "LAX"},
            "LHR": {"name": "Heathrow Airport", "city": "london", "iata": "LHR"},
            "CDG": {"name": "Charles de Gaulle Airport", "city": "paris", "iata": "CDG"},
            "HND": {"name": "Tokyo Haneda Airport", "city": "tokyo", "iata": "HND"},
            "SYD": {"name": "Sydney Airport", "city": "sydney", "iata": "SYD"}
        }
    
    def get_city(self, city_name):
        """Get city data by name."""
        key = city_name.lower().strip()
        return self._cities.get(key)
    
    def get_airport(self, code):
        """Get airport data by IATA code."""
        key = code.upper().strip()
        return self._airports.get(key)
    
    def get_country(self, code):
        """Get country data by code."""
        key = code.upper().strip()
        return self._countries.get(key)
    
    def get_airports_by_city(self, city_name):
        """Get all airports for a given city."""
        key = city_name.lower().strip()
        return [airport for code, airport in self._airports.items() if airport['city'] == key]
    
    def search_cities(self, query):
        """Search for cities by name prefix."""
        query = query.lower().strip()
        return {k: v for k, v in self._cities.items() if k.startswith(query)}
    
    def search_airports(self, query):
        """Search for airports by name or code."""
        query = query.strip()
        results = {}
        
        # Search by IATA code
        if query.upper() in self._airports:
            results[query.upper()] = self._airports[query.upper()]
        
        # Search by name
        query_lower = query.lower()
        for code, airport in self._airports.items():
            if query_lower in airport['name'].lower():
                results[code] = airport
        
        return results

# Initialize global location data
location_data = LocationData()

def normalize_location_name(location_name):
    """
    Normalize location name by removing extra spaces and standardizing format.
    
    Args:
        location_name (str): Location name to normalize
        
    Returns:
        str: Normalized location name
    """
    if not location_name:
        return ""
    
    # Remove extra spaces, convert to title case
    return " ".join(location_name.strip().split()).title()

def is_valid_city(city_name):
    """
    Check if the provided name is a valid city.
    
    Args:
        city_name (str): City name to validate
        
    Returns:
        bool: True if valid city, False otherwise
    """
    if not city_name:
        return False
    
    normalized = city_name.lower().strip()
    return normalized in location_data._cities

def is_valid_airport_code(code):
    """
    Check if the provided code is a valid IATA airport code.
    
    Args:
        code (str): Airport code to validate
        
    Returns:
        bool: True if valid airport code, False otherwise
    """
    if not code:
        return False
    
    # IATA codes are 3 uppercase letters
    if not re.match(r'^[A-Z]{3}$', code.upper()):
        return False
    
    return code.upper() in location_data._airports

def get_suggested_locations(partial_name, limit=5):
    """
    Get location suggestions based on partial input.
    
    Args:
        partial_name (str): Partial location name
        limit (int): Maximum number of suggestions to return
        
    Returns:
        list: List of suggested location names
    """
    if not partial_name or len(partial_name) < 2:
        return []
    
    normalized = partial_name.lower().strip()
    
    # Search cities
    city_matches = [city_data["name"] for _, city_data in location_data._cities.items() 
                    if _.startswith(normalized)]
    
    # Search airports
    airport_matches = [f"{airport_data['name']} ({code})" 
                      for code, airport_data in location_data._airports.items() 
                      if airport_data['name'].lower().startswith(normalized) or 
                      code.lower().startswith(normalized)]
    
    # Combine and limit results
    all_matches = city_matches + airport_matches
    return all_matches[:limit]

def get_airport_for_city(city_name):
    """
    Get the main airport for a given city.
    
    Args:
        city_name (str): City name
        
    Returns:
        dict: Airport data or None if not found
    """
    if not is_valid_city(city_name):
        return None
    
    airports = location_data.get_airports_by_city(city_name.lower().strip())
    if not airports:
        return None
    
    # Simply return the first airport (in a real app, you might have logic to select the main one)
    return airports[0]

def get_distance_between_locations(location1, location2):
    """
    Calculate approximate distance between two locations.
    
    Note: This is a placeholder function. In a real application, you would use
    geolocation coordinates and the haversine formula or a mapping API.
    
    Args:
        location1 (str): First location name
        location2 (str): Second location name
        
    Returns:
        float: Approximate distance in kilometers or None if not calculable
    """
    # This would be implemented with real geolocation data
    # For now, return a placeholder message
    return None

def get_timezone_for_location(location_name):
    """
    Get timezone information for a location.
    
    Note: This is a placeholder function. In a real application, you would use
    a timezone database or API.
    
    Args:
        location_name (str): Location name
        
    Returns:
        str: Timezone name or None if not found
    """
    # This would be implemented with real timezone data
    # For now, return a placeholder
    return None

def is_domestic_travel(origin, destination):
    """
    Determine if travel between two locations is domestic.
    
    Args:
        origin (str): Origin city name
        destination (str): Destination city name
        
    Returns:
        bool: True if domestic travel, False if international, None if undetermined
    """
    if not (is_valid_city(origin) and is_valid_city(destination)):
        return None
    
    origin_data = location_data.get_city(origin.lower().strip())
    dest_data = location_data.get_city(destination.lower().strip())
    
    if not (origin_data and dest_data):
        return None
    
    # Check if both cities are in the same country
    return origin_data['country'] == dest_data['country']

def get_popular_destinations():
    """
    Get a list of popular travel destinations.
    
    Returns:
        list: List of popular destination names
    """
    # In a real app, this might be based on current trends or season
    return [city_data['name'] for _, city_data in 
            sorted(location_data._cities.items(), 
                  key=lambda x: x[1]['population'], 
                  reverse=True)[:5]]

def validate_location_pair(origin, destination):
    """
    Validate that both origin and destination are valid and not the same.
    
    Args:
        origin (str): Origin location
        destination (str): Destination location
        
    Returns:
        bool: True if valid pair, False otherwise
    """
    if not (origin and destination):
        return False
    
    # Check if both are valid cities
    if not (is_valid_city(origin) and is_valid_city(destination)):
        return False
    
    # Check that origin and destination are not the same
    return origin.lower().strip() != destination.lower().strip()

def find_iata_code(location_name):
    """
    Find IATA code for a given location name.
    This is a simplified version that works with our sample data.
    
    Args:
        location_name (str): Location name to search for
        
    Returns:
        dict: Dictionary with 'name' and 'iata' keys, or None if not found
    """
    if not location_name:
        return None
        
    # Check for direct IATA code input
    if len(location_name) == 3 and location_name.isalpha():
        code = location_name.upper()
        if is_valid_airport_code(code):
            airport = location_data.get_airport(code)
            return {'name': airport['name'], 'iata': code}
    
    # Try to find by city name
    location_name_lower = location_name.lower().strip()
    
    # Check if it's a city we know
    if is_valid_city(location_name):
        city_data = location_data.get_city(location_name_lower)
        # Find the main airport for this city
        airports = location_data.get_airports_by_city(location_name_lower)
        if airports:
            return {'name': city_data['name'], 'iata': airports[0]['iata']}
    
    # Try partial matching for cities
    for city_key, city_data in location_data._cities.items():
        if location_name_lower in city_key or city_key in location_name_lower:
            # Find the main airport for this city
            airports = location_data.get_airports_by_city(city_key)
            if airports:
                return {'name': city_data['name'], 'iata': airports[0]['iata']}
    
    # Try airports directly
    airport_matches = location_data.search_airports(location_name)
    if airport_matches:
        first_key = next(iter(airport_matches))
        airport = airport_matches[first_key]
        return {'name': airport['name'], 'iata': airport['iata']}
    
    # No matches found
    return None