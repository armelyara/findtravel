"""
Flight service for managing flight-related operations
"""
from typing import Dict, Optional, Any, List
import requests
from datetime import datetime
from services.api_service import AmadeusTokenManager, LocationService
from models.travel_plan import TravelPlan
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from utils.date_utils import validate_date_format as validate_date
from utils.input_utils import get_numeric_input, get_date_input


class FlightService:
    """Service for flight search and booking"""
    
    # Airline names mapping
    AIRLINE_NAMES = {
        'AA': 'American Airlines',
        'DL': 'Delta Air Lines',
        'UA': 'United Airlines',
        'AF': 'Air France',
        'BA': 'British Airways',
        'LH': 'Lufthansa',
        'EK': 'Emirates',
        'SQ': 'Singapore Airlines',
        'QF': 'Qantas',
        'CX': 'Cathay Pacific',
        'JL': 'Japan Airlines',
        'AY': 'Finnair',
        'IB': 'Iberia',
        'KL': 'KLM',
        'OS': 'Austrian Airlines',
        'LX': 'Swiss International Air Lines'
    }
    
    def __init__(self, amadeus_client_id: str, amadeus_client_secret: str, google_maps_key: str, llm: Any):
        self.amadeus_token_manager = AmadeusTokenManager(amadeus_client_id, amadeus_client_secret)
        self.location_service = LocationService(
            google_maps_key = google_maps_key,
            token_manager=self.amadeus_token_manager)
        self.llm = llm
        self.access_token = self.amadeus_token_manager.get_token()
        
    def search_flights(self, travel_plan: TravelPlan) -> None:
        """Search flights using the Amadeus API"""
        # Ensure we have tokens and valid inputs
        if not self._validate_search_criteria(travel_plan):
            return
            
        # Get flight data from Amadeus
        flight_options = self.search_amadeus_flights(travel_plan)
        
        if flight_options and 'data' in flight_options and flight_options['data']:
            # Format the flight data
            formatted_flights = self.format_flight_data(flight_options, travel_plan)
            
            # Display the flight options to the user
            print(f"Here are your flight options from {travel_plan.departure['name']} to {travel_plan.destination['name']}:\n\n{formatted_flights}")
            
            # Use a direct prompt template approach instead of chains with memory
            inquiry_template = """You're a helpful flight booking assistant.
            The user has flight options as follows:
            
            {flight_options}
            
            The user's question or input is: {question}
            
            If the user appears to be selecting a flight option (mentioning options like 'Option 1' or similar), inform them to use the number-only input to make a selection.
            Otherwise, provide a detailed and helpful response about the flight options specifically addressing the user's question."""
            
            # Display booking options
            print("\nSelect a flight to book or ask questions about the options.")
            print("Enter 'X' to skip flight booking (not recommended).")
            
            while True:
                user_input = input("\nChoice (1-3) or question: ").strip().upper()
                
                if user_input == 'X':
                    print("\n⚠️ Skipping flight booking. This may limit your other travel options.")
                    return
                    
                if user_input in ('1', '2', '3'):
                    option_index = int(user_input) - 1
                    
                    # Check if this option is available
                    if option_index < len(flight_options['data']):
                        selected = flight_options['data'][option_index]
                        # Extract price as float
                        price = float(selected['price']['total'])
                        
                        print(f"\nSelected Option {user_input}: ${price:.2f}")
                        
                        # Check if price is within budget
                        if price <= travel_plan.remaining_budget:
                            confirm = input("Confirm booking? (y/n): ").lower()
                            
                            if confirm == 'y':
                                travel_plan.flights = {
                                    'option': int(user_input),
                                    'price': price,
                                    'details': self.format_flight_data(flight_options, travel_plan)
                                }
                                travel_plan.remaining_budget -= price
                                print(f"✅ Flight booked! Remaining budget: ${travel_plan.remaining_budget:.2f}")
                                break
                        else:
                            print(f"⚠️ This flight costs ${price:.2f}, which exceeds your remaining budget of ${travel_plan.remaining_budget:.2f}.")
                            modify = input("Would you like to increase your budget? (y/n): ").lower()
                            
                            if modify == 'y':
                                new_budget = get_numeric_input("Enter new total budget (USD): ", min_value=travel_plan.total_budget)
                                budget_increase = new_budget - travel_plan.total_budget
                                travel_plan.total_budget = new_budget
                                travel_plan.remaining_budget += budget_increase
                                print(f"Budget increased to ${new_budget:.2f}. Remaining: ${travel_plan.remaining_budget:.2f}")
                    else:
                        print(f"Invalid option. Please select a number between 1 and {len(flight_options['data'])}.")
                else:
                    # Use direct prompt instead of chain with memory
                    filled_prompt = inquiry_template.format(
                        flight_options=formatted_flights,
                        question=user_input
                    )
                    # Call the LLM directly with correct output handling
                    response = str(self.llm.invoke(filled_prompt))
                    print(f"\nAssistant: {response}")
        else:
            # No flights found - show modification options
            self._handle_no_flights_found(travel_plan)
    
    def search_amadeus_flights(self, travel_plan: TravelPlan) -> Dict:
        """Search flights using the Amadeus API"""
        # Ensure we have valid tokens
        if not self.access_token:
            self.access_token = self.amadeus_token_manager.get_token()
            
        if not self.access_token:
            print("⚠️ Unable to authenticate with Amadeus API")
            return {}
            
        # Get the IATA codes from the travel plan
        origin = travel_plan.departure.get('iata')
        destination = travel_plan.destination.get('iata')
        
        # Prepare API parameters
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": travel_plan.departure_date,
            "returnDate": travel_plan.return_date,
            "adults": travel_plan.travelers,
            "max": 3,  # Limit to 3 options for simplicity
            "currencyCode": "USD"
        }
        
        try:
            print(f"\n🔍 Searching for flights from {origin} to {destination}...")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Token expired, refresh and try again
                print("Token expired. Refreshing...")
                self.access_token = self.amadeus_token_manager.get_token()
                
                if self.access_token:
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.get(url, headers=headers, params=params)
                    
                    if response.status_code == 200:
                        return response.json()
            
            print(f"⚠️ API Error: {response.status_code} - {response.text}")
            return {}
            
        except Exception as e:
            print(f"⚠️ Error searching flights: {str(e)}")
            return {}
            
    def format_flight_data(self, flight_data: Dict, travel_plan: TravelPlan) -> str:
        """Format flight data in a readable way"""
        if not flight_data or 'data' not in flight_data or not flight_data['data']:
            return "No flights found."
            
        formatted = ""
        for i, option in enumerate(flight_data['data'][:3], 1):
            price = float(option['price']['total'])
            price_status = "✅ Within budget" if price <= travel_plan.remaining_budget else "❌ Exceeds budget"
            
            formatted += f"[OPTION {i}] ${price:.2f} {price_status}\n"
            
            # Format outbound flight
            outbound = option['itineraries'][0]
            formatted += f"OUTBOUND ({outbound['duration']})\n"
            formatted += f"Airline: {self._get_airline_name(outbound['segments'][0]['carrierCode'])}\n"
            formatted += f"Stops: {len(outbound['segments']) - 1}\n"
            
            for segment in outbound['segments']:
                dep_time = segment['departure']['at'].replace('T', ' ').split('+')[0]
                arr_time = segment['arrival']['at'].replace('T', ' ').split('+')[0]
                formatted += f"• {segment['departure']['iataCode']} → {segment['arrival']['iataCode']} "
                formatted += f"({dep_time} → {arr_time})\n"
            
            # Format return flight if available
            if len(option['itineraries']) > 1:
                return_flight = option['itineraries'][1]
                formatted += f"RETURN ({return_flight['duration']})\n"
                formatted += f"Airline: {self._get_airline_name(return_flight['segments'][0]['carrierCode'])}\n"
                formatted += f"Stops: {len(return_flight['segments']) - 1}\n"
                
                for segment in return_flight['segments']:
                    dep_time = segment['departure']['at'].replace('T', ' ').split('+')[0]
                    arr_time = segment['arrival']['at'].replace('T', ' ').split('+')[0]
                    formatted += f"• {segment['departure']['iataCode']} → {segment['arrival']['iataCode']} "
                    formatted += f"({dep_time} → {arr_time})\n"
            
            formatted += "Price: $" + str(price) + "\n\n"
            
        return formatted
            
    def get_flight_summary(self, travel_plan: TravelPlan) -> str:
        """Return a summary of booked flight information"""
        if not travel_plan.flights:
            return "No flight booked yet."
            
        return f"""✈️ FLIGHT BOOKING SUMMARY
From: {travel_plan.departure['name']} ({travel_plan.departure['iata']})
To: {travel_plan.destination['name']} ({travel_plan.destination['iata']})
Dates: {travel_plan.departure_date} to {travel_plan.return_date}
Option: {travel_plan.flights.get('option')}
Total Price: ${travel_plan.flights.get('price', 0):.2f}"""
            
    def _get_airline_name(self, carrier_code: str) -> str:
        """Get airline name from carrier code"""
        return self.AIRLINE_NAMES.get(carrier_code, carrier_code)
        
    def _validate_search_criteria(self, travel_plan: TravelPlan) -> bool:
        """Validate flight search criteria"""
        # Check if we have all required data
        if not travel_plan.departure or not travel_plan.departure.get('iata'):
            print("⚠️ Missing departure information.")
            travel_plan.departure = self.get_location_input("Enter departure city/airport: ")
            
        if not travel_plan.destination or not travel_plan.destination.get('iata'):
            print("⚠️ Missing destination information.")
            travel_plan.destination = self.get_location_input("Enter destination city/airport: ")
            
        # Validate dates
        today = datetime.now().strftime("%Y-%m-%d")
        
        if not travel_plan.departure_date or not validate_date(travel_plan.departure_date):
            print("⚠️ Invalid departure date.")
            travel_plan.departure_date = get_date_input(
                "Enter departure date (YYYY-MM-DD): ", 
                min_date=today
            )
            
        if not travel_plan.return_date or not validate_date(travel_plan.return_date):
            print("⚠️ Invalid return date.")
            travel_plan.return_date = get_date_input(
                "Enter return date (YYYY-MM-DD): ", 
                min_date=travel_plan.departure_date
            )
            
        # Validate travelers
        if not travel_plan.travelers or travel_plan.travelers < 1:
            print("⚠️ Invalid number of travelers.")
            travel_plan.travelers = int(get_numeric_input("Enter number of travelers: ", min_value=1))
            
        # All checks passed
        return True
        
    def get_location_input(self, prompt: str) -> Dict[str, str]:
        """Get and validate location input, returning both name and IATA code"""
        while True:
            location = input(prompt).strip()
            
            # Use location service to find IATA code
            location_data = self.location_service.find_iata_code(location)
            
            if location_data:
                return location_data
            else:
                print(f"⚠️ Could not find IATA code for '{location}'. Please try another location or format.")
    
    def modify_flight_criteria(self, travel_plan: TravelPlan) -> None:
        """Allow user to modify flight search criteria"""
        self._handle_no_flights_found(travel_plan)
        
    def _handle_no_flights_found(self, travel_plan: TravelPlan) -> None:
        """Handle the case when no flights are found"""
        while True:
            print("\nWhat would you like to change?")
            print(f"1. Departure city (currently: {travel_plan.departure['name']})")
            print(f"2. Destination city (currently: {travel_plan.destination['name']})")
            print(f"3. Travel dates (currently: {travel_plan.departure_date} to {travel_plan.return_date})")
            print(f"4. Budget (currently: ${travel_plan.total_budget})")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == '1':
                travel_plan.departure = self.get_location_input("New departure city/airport: ")
                break
            elif choice == '2':
                travel_plan.destination = self.get_location_input("New destination city/airport: ")
                break
            elif choice == '3':
                # Get today's date for validation
                today = datetime.now().strftime("%Y-%m-%d")
                
                travel_plan.departure_date = get_date_input(
                    "New departure date (YYYY-MM-DD): ", 
                    min_date=today
                )
                
                travel_plan.return_date = get_date_input(
                    "New return date (YYYY-MM-DD): ", 
                    min_date=today,
                    reference_date=travel_plan.departure_date
                )
                break
            elif choice == '4':
                travel_plan.total_budget = get_numeric_input("New total budget (USD): ", min_value=100)
                travel_plan.remaining_budget = travel_plan.total_budget
                break
            elif choice == '5':
                return
            else:
                print("Invalid input. Please enter a number between 1 and 5.")
                
    def answer_question(self, question, flight_data):
        """Answer questions about flight options."""
        prompt = f"""As a travel assistant, answer this question about flight options:
        
        Flight options:
        {flight_data}
        
        Question: {question}
        
        Provide a helpful, detailed response about the flights."""
        
        response = self.llm.invoke(prompt)
        return str(response)