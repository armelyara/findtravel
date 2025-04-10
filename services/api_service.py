"""
API service for external API interactions
"""
import time
import requests
from typing import Dict, Optional, Any
import googlemaps


class AmadeusTokenManager:
    """Responsible for managing Amadeus API tokens with better error handling"""
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.expiry_time = 0
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def get_token(self) -> Optional[str]:
        """Get Amadeus API token with improved caching and retry logic"""
        # Return cached token if still valid (with 5-min buffer)
        if self.token and time.time() < (self.expiry_time - 300):
            return self.token
            
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        # Implement retry logic with exponential backoff
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.post(url, headers=headers, data=data, timeout=5)
                if response.status_code == 200:
                    token_data = response.json()
                    self.token = token_data.get('access_token')
                    self.expiry_time = time.time() + token_data.get('expires_in', 1800)
                    return self.token
                elif response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get('Retry-After', self.retry_delay * (2 ** retries)))
                    print(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"Amadeus token error {response.status_code}: {response.text}")
                    if response.status_code >= 500:  # Server error, retry
                        time.sleep(self.retry_delay * (2 ** retries))
                    else:  # Client error, no retry
                        break
            except requests.exceptions.RequestException as e:
                print(f"Network error fetching Amadeus token: {e}")
                time.sleep(self.retry_delay * (2 ** retries))
                
            retries += 1
        
        return None


class LocationService:
    """Service for managing location data and lookups"""
    def __init__(self, google_maps_key: str, token_manager: AmadeusTokenManager):
        self.token_manager = token_manager
        self.google_maps_key = google_maps_key
        self.location_cache = {}
        
        # Special cases for locations that might be difficult to find
        self.special_cases = {
            'abidjan': ('ABJ', 'Abidjan'),
            'maroc': ('CMN', 'Casablanca'),
            'casablanca': ('CMN', 'Casablanca'),
            'kigali': ('KGL', 'Kigali'),
            'nairobi': ('NBO', 'Nairobi'),
            'dakar': ('DKR', 'Dakar')
        }
        
    def find_iata_code(self, location_name: str) -> Optional[Dict[str, str]]:
        """Find IATA code for global cities with improved recognition"""
        import difflib
        import googlemaps
        
        # Check cache first
        if location_name.lower() in self.location_cache:
            return self.location_cache[location_name.lower()]
        
        # Check special cases
        lower_input = location_name.lower()
        if lower_input in self.special_cases:
            result = {'iata': self.special_cases[lower_input][0], 'name': self.special_cases[lower_input][1]}
            self.location_cache[lower_input] = result
            return result
            
        # Try Amadeus API first
        token = self.token_manager.get_token()
        if token:
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "subType": "CITY,AIRPORT",
                "keyword": location_name,
                "page[limit]": 5
            }
            try:
                response = requests.get(
                    "https://test.api.amadeus.com/v1/reference-data/locations",
                    headers=headers,
                    params=params
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        best_match = self._find_best_match(location_name, data['data'])
                        result = {
                            'iata': best_match['iataCode'],
                            'name': best_match['name']
                        }
                        self.location_cache[lower_input] = result
                        return result
            except Exception as e:
                print(f"API Amadeus error: {e}")
                
        # Fallback to Google Maps
        try:
            gmaps = googlemaps.Client(key=self.google_maps_key)
            geocode_result = gmaps.geocode(location_name)
            if geocode_result:
                for component in geocode_result[0]['address_components']:
                    if 'locality' in component['types'] or 'administrative_area_level_1' in component['types']:
                        city_name = component['long_name']
                        return self.find_iata_code(city_name)  # Try again with the city name
        except Exception as e:
            print(f"Google Maps error: {e}")
            
        return None
        
    def _find_best_match(self, input_name: str, locations: list) -> Dict:
        """Find best match using similarity algorithm"""
        import difflib
        
        input_name = input_name.lower()
        best_score = 0
        best_match = locations[0]

        for loc in locations:
            loc_name = loc['name'].lower()
            score = difflib.SequenceMatcher(None, input_name, loc_name).ratio()
            if input_name == loc_name:
                score += 0.5
            if score > best_score:
                best_score = score
                best_match = loc

        return best_match