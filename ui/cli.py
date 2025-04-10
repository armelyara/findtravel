import sys
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from models.travel_plan import TravelPlan
from services.api_wrappers import search_flights, format_flight_data, get_hotel_suggestions, get_activity_suggestions
from utils.date_utils import validate_date_format
from utils.location_utils import find_iata_code

class TravelPlannerCLI:
    """Command-line interface for the Travel Planner application."""
    
    def __init__(self, travel_plan: TravelPlan, flight_service=None, hotel_service=None, activity_service=None):
        """Initialize the CLI with a travel plan and services.
        
        Args:
            travel_plan: The travel plan model to manage data
            flight_service: Optional flight service instance
            hotel_service: Optional hotel service instance
            activity_service: Optional activity service instance
        """
        self.travel_plan = travel_plan
        self.flight_service = flight_service
        self.hotel_service = hotel_service
        self.activity_service = activity_service
        self.done = False

    def display_header(self, title: str) -> None:
        """Display a formatted header.
        
        Args:
            title: The title to display
        """
        print(f"\n{'✨'*10}")
        print(f"🌟 {title} 🌟")
        print(f"{'✨'*10}")

    def display_welcome(self) -> None:
        """Display welcome message."""
        self.display_header("Travel Planning Assistant")
        print("\n🌍 Welcome to the Travel Planning Assistant! 🌍")
        print("✈️  This tool will help you plan your next dream vacation  🏝️")
        print("🧳 Including flights, hotels, and exciting activities! 🎭")

    def get_text_input(self, prompt: str, required: bool = True) -> str:
        """Get text input from user with validation.
        
        Args:
            prompt: The prompt to display
            required: Whether input is required
            
        Returns:
            User input string
        """
        while True:
            value = input(prompt).strip()
            if value or not required:
                return value
            print("This field is required. Please try again.")

    def get_numeric_input(self, prompt: str, min_value: float = 0, 
                          max_value: float = float('inf'), 
                          integer_only: bool = False) -> float:
        """Get numeric input from user with validation.
        
        Args:
            prompt: The prompt to display
            min_value: Minimum acceptable value
            max_value: Maximum acceptable value
            integer_only: Whether to require an integer
            
        Returns:
            Numeric value from user
        """
        while True:
            try:
                value = input(prompt).strip()
                if not value:
                    print("This field is required. Please try again.")
                    continue
                
                num = int(value) if integer_only else float(value)
                
                if num < min_value or num > max_value:
                    print(f"Please enter a value between {min_value} and {max_value}.")
                    continue
                    
                return num
            except ValueError:
                print("Please enter a valid number.")

    def get_date_input(self, prompt: str, min_date: Optional[datetime] = None) -> str:
        """Get date input from user with validation.
        
        Args:
            prompt: The prompt to display
            min_date: Minimum acceptable date
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        while True:
            date_str = input(prompt).strip()
            
            if not validate_date_format(date_str):
                print("Invalid date format. Please use YYYY-MM-DD.")
                continue
                
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            if min_date and date_obj < min_date:
                print(f"Date must be on or after {min_date.strftime('%Y-%m-%d')}.")
                continue
                
            return date_str

    def get_location_input(self, prompt: str) -> Dict[str, str]:
        """Get location input from user with validation and suggestions.
        
        Args:
            prompt: The prompt to display
            
        Returns:
            Dictionary with location name and IATA code
        """
        while True:
            location = self.get_text_input(f"🌍 {prompt}")
            
            # Handle direct IATA code input
            if len(location) == 3 and location.isalpha():
                confirm = input(f"🤔 Did you mean the airport code '{location.upper()}'? (y/n): ").lower()
                if confirm == 'y':
                    print(f"✅ Airport code {location.upper()} confirmed!")
                    return {'name': location.upper(), 'iata': location.upper()}
            
            # Find location using API
            print(f"🔍 Searching for location: {location}...")
            result = find_iata_code(location)
            if result:
                print(f"✅ Found: {result['name']} ({result['iata']})")
                return result
            
            print("""❌ Location not recognized. 

💡 Try these tips:
  🔹 Use the international name (e.g. 'Casablanca' instead of 'Dar el Beida')
  🔹 For countries, specify a city (e.g. 'Abidjan' instead of 'Ivory Coast')
  🔹 Try adding 'Airport' (e.g. 'Bamako Airport')
  🔹 For major cities, try using their common name (e.g. 'Paris', 'London')
""")

    def collect_initial_details(self) -> None:
        """Collect initial travel details from user."""
        self.display_welcome()
        
        print("\n📌 Let's plan your trip! First, I need some basic information:")
        print("─────────────────────────────────────────────────────")
        
        self.travel_plan.departure = self.get_location_input("\nDeparture city/airport")
        self.travel_plan.destination = self.get_location_input("Destination city/airport")
        
        print("\n📅 Now, let's set the dates for your journey:")
        print("─────────────────────────────────────────────────────")
        
        today = datetime.now()
        self.travel_plan.departure_date = self.get_date_input(
            "📆 Departure date (YYYY-MM-DD): ", 
            min_date=today
        )
        
        departure_date_obj = datetime.strptime(self.travel_plan.departure_date, "%Y-%m-%d")
        self.travel_plan.return_date = self.get_date_input(
            "📆 Return date (YYYY-MM-DD): ", 
            min_date=departure_date_obj
        )
        
        print("\n👥 Trip details:")
        print("─────────────────────────────────────────────────────")
        
        self.travel_plan.travelers = self.get_numeric_input(
            "👨‍👩‍👧‍👦 Number of travelers: ", 
            min_value=1, 
            max_value=10, 
            integer_only=True
        )
        
        self.travel_plan.total_budget = self.get_numeric_input(
            "💰 Total budget (USD): ", 
            min_value=100
        )
        
        self.travel_plan.remaining_budget = self.travel_plan.total_budget
        
        print("\n✨ Great! Your trip details are set! Here's a summary:")
        self.display_travel_summary()

    def display_travel_summary(self) -> None:
        """Display a summary of the current travel plan."""
        self.display_header("TRAVEL PLAN SUMMARY")
        
        print("\n┌─────────────── TRIP DETAILS ───────────────┐")
        print(f"│  🛫 From:      {self.travel_plan.departure['name']} ({self.travel_plan.departure['iata']})".ljust(50) + "│")
        print(f"│  🛬 To:        {self.travel_plan.destination['name']} ({self.travel_plan.destination['iata']})".ljust(50) + "│")
        print(f"│  📅 Dates:     {self.travel_plan.departure_date} to {self.travel_plan.return_date}".ljust(50) + "│")
        print(f"│  👥 Travelers: {self.travel_plan.travelers}".ljust(50) + "│")
        print("└───────────────────────────────────────────┘")
        
        print("\n┌─────────────── BUDGET INFO ───────────────┐")
        print(f"│  💰 Total Budget:  ${self.travel_plan.total_budget:.2f}".ljust(50) + "│")
        print(f"│  💵 Remaining:     ${self.travel_plan.remaining_budget:.2f}".ljust(50) + "│")
        print("└───────────────────────────────────────────┘")
        
        if self.travel_plan.flights or self.travel_plan.hotels or self.travel_plan.activities:
            print("\n┌─────────────── BOOKINGS ──────────────────┐")
            if self.travel_plan.flights:
                print(f"│  ✈️  Flight:     Option {self.travel_plan.flights['option']} - ${self.travel_plan.flights['price']:.2f}".ljust(50) + "│")
                
            if self.travel_plan.hotels:
                print(f"│  🏨 Hotel:      Option {self.travel_plan.hotels['option']} - ${self.travel_plan.hotels['price']:.2f}".ljust(50) + "│")
                
            if self.travel_plan.activities:
                activity_cost = sum(act.get('price', 0) for act in self.travel_plan.activities)
                print(f"│  🎭 Activities: {len(self.travel_plan.activities)} booked - ${activity_cost:.2f}".ljust(50) + "│")
            print("└───────────────────────────────────────────┘")

    def show_main_menu(self) -> None:
        """Display the main menu and process selection."""
        while not self.done:
            self.display_header("MAIN MENU")
            
            print("1️⃣  View/Edit Travel Details  📝")
            print("2️⃣  Search and Book Flights   ✈️")
            print("3️⃣  Search and Book Hotels    🏨")
            print("4️⃣  Search and Book Activities 🎭")
            print("5️⃣  View Full Itinerary       📋")
            print("6️⃣  Save Itinerary            💾")
            print("7️⃣  Exit                      👋")
            
            choice = self.get_text_input("\n🔍 Enter your choice (1-7): ")
            
            if choice == '1':
                self.edit_travel_details()
            elif choice == '2':
                self.discuss_flights()
            elif choice == '3':
                self.discuss_hotels()
            elif choice == '4':
                self.discuss_activities()
            elif choice == '5':
                self.display_full_itinerary()
            elif choice == '6':
                self.save_itinerary()
            elif choice == '7':
                self.done = True
                print("\nThank you for using the Travel Planning Assistant. Goodbye!")
            else:
                print("Invalid choice. Please enter a number between 1 and 7.")

    def edit_travel_details(self) -> None:
        """Edit basic travel details."""
        self.display_header("EDIT TRAVEL DETAILS")
        self.display_travel_summary()
        
        print("\n✏️ What would you like to change?")
        print(f"1️⃣ Departure location       🛫 Currently: {self.travel_plan.departure['name']}")
        print(f"2️⃣ Destination location     🛬 Currently: {self.travel_plan.destination['name']}")
        print(f"3️⃣ Travel dates             📅 Currently: {self.travel_plan.departure_date} to {self.travel_plan.return_date}")
        print(f"4️⃣ Number of travelers      👥 Currently: {self.travel_plan.travelers}")
        print(f"5️⃣ Budget                   💰 Currently: ${self.travel_plan.total_budget:.2f}")
        print("6️⃣ Back to main menu        ↩️")
        
        choice = self.get_text_input("\n🔍 Enter your choice (1-6): ")
        
        if choice == '1':
            self.travel_plan.departure = self.get_location_input("New departure city/airport: ")
            print("✅ Departure location updated!")
        elif choice == '2':
            self.travel_plan.destination = self.get_location_input("New destination city/airport: ")
            print("✅ Destination location updated!")
        elif choice == '3':
            today = datetime.now()
            self.travel_plan.departure_date = self.get_date_input(
                "New departure date (YYYY-MM-DD): ", 
                min_date=today
            )
            
            departure_date_obj = datetime.strptime(self.travel_plan.departure_date, "%Y-%m-%d")
            self.travel_plan.return_date = self.get_date_input(
                "New return date (YYYY-MM-DD): ", 
                min_date=departure_date_obj
            )
            print("✅ Travel dates updated!")
        elif choice == '4':
            self.travel_plan.travelers = self.get_numeric_input(
                "New number of travelers: ", 
                min_value=1, 
                max_value=10, 
                integer_only=True
            )
            print("✅ Number of travelers updated!")
        elif choice == '5':
            if self.travel_plan.flights or self.travel_plan.hotels or self.travel_plan.activities:
                print("⚠️ Warning: Changing budget will reset all bookings. Continue? (y/n)")
                confirm = self.get_text_input("").lower()
                if confirm != 'y':
                    return
                
                # Reset bookings
                self.travel_plan.flights = None
                self.travel_plan.hotels = None
                self.travel_plan.activities = []
            
            self.travel_plan.total_budget = self.get_numeric_input(
                "New total budget (USD): ", 
                min_value=100
            )
            self.travel_plan.remaining_budget = self.travel_plan.total_budget
            print("✅ Budget updated!")
        elif choice == '6':
            return
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")
            
        self.display_travel_summary()

    def discuss_flights(self) -> None:
        """Interactive flight search and booking."""
        self.display_header("FLIGHT SEARCH")
        
        if not self.travel_plan.departure or not self.travel_plan.destination:
            print("⚠️ Please set departure and destination first!")
            return
        
        # If flight service exists, use its conversational interface
        if self.flight_service:
            # Use the service's search_flights method
            self.flight_service.search_flights(self.travel_plan)
            return
            
        # Otherwise fall back to basic functionality
        print(f"\n🔍 Searching flights from {self.travel_plan.departure['name']} to {self.travel_plan.destination['name']}...")
        print("✈️ This might take a moment, please wait...")
        
        # Fall back to the imported functions
        flight_data = search_flights(
            self.travel_plan.departure['iata'],
            self.travel_plan.destination['iata'],
            self.travel_plan.departure_date,
            self.travel_plan.return_date,
            self.travel_plan.travelers,
            self.travel_plan.remaining_budget
        )
        # Format flight data for display
        formatted_flights = format_flight_data(flight_data, self.travel_plan)
        print(formatted_flights)
        
        if "No flights found" in formatted_flights:
            print("\n❓ Would you like to modify your search criteria? (y/n)")
            modify = self.get_text_input("").lower()
            if modify == 'y':
                self.edit_travel_details()
            return
        
        # Booking interaction
        print("\n┌─────────────── FLIGHT OPTIONS ───────────────┐")
        print("│  1️⃣  Select Option 1                        │")
        print("│  2️⃣  Select Option 2                        │")
        print("│  3️⃣  Select Option 3                        │")
        print("│  ❌  [X] Go back to main menu               │")
        print("└───────────────────────────────────────────────┘")
        
        while True:
            choice = self.get_text_input("\n✈️ Choose your flight (1-3) or [X] to go back: ").upper()
            
            if choice == 'X':
                return
                
            if choice in ('1', '2', '3'):
                try:
                    # Get the price from selected flight data
                    selected_index = int(choice) - 1
                    if selected_index < 0 or selected_index >= len(flight_data.get('data', [])):
                        print("❌ Invalid option number.")
                        continue
                        
                    selected = flight_data['data'][selected_index]
                    price = float(selected['price']['total'])
                    
                    # Confirm booking
                    print(f"\n💲 Option {choice} costs ${price:.2f}")
                    confirm = self.get_text_input("✅ Confirm booking? (y/n): ").lower()
                    
                    if confirm == 'y':
                        if price <= self.travel_plan.remaining_budget:
                            self.travel_plan.flights = {
                                'option': int(choice),
                                'price': price,
                                'details': formatted_flights
                            }
                            self.travel_plan.remaining_budget -= price
                            print(f"\n🎉 Flight option {choice} booked successfully!")
                            print(f"💰 Remaining budget: ${self.travel_plan.remaining_budget:.2f}")
                            return
                        else:
                            print(f"⚠️ This flight costs ${price:.2f}, which exceeds your budget of ${self.travel_plan.remaining_budget:.2f}!")
                            print("💡 You can increase your budget in the Travel Details menu.")
                except (IndexError, KeyError):
                    print("❌ Error processing flight data. Please try again.")
            else:
                print("❓ Please enter a valid option (1-3) or X to go back.")

    def discuss_hotels(self) -> None:
        """Interactive hotel search and booking."""
        self.display_header("HOTEL SEARCH")
        
        if not self.travel_plan.flights:
            print("\n✈️ Please book flights first!")
            return
            
        # Calculate stay duration
        departure_date_obj = datetime.strptime(self.travel_plan.departure_date, "%Y-%m-%d")
        return_date_obj = datetime.strptime(self.travel_plan.return_date, "%Y-%m-%d")
        nights = (return_date_obj - departure_date_obj).days
        
        print(f"\nSearching hotels in {self.travel_plan.destination['name']} for {nights} nights...")
        
        # Get hotel suggestions
        if self.hotel_service:
            # Use the service instance
            self.hotel_service.discuss_hotels(self.travel_plan)
            return  # Hotel service handles the rest of the interaction
        else:
            # Fall back to the API wrappers
            hotel_suggestions = get_hotel_suggestions(
                self.travel_plan.destination['name'],
                self.travel_plan.remaining_budget,
                nights,
                self.travel_plan.travelers
            )
        
        print(f"\n{'='*60}\n🏨 RECOMMENDED HOTELS IN {self.travel_plan.destination['name'].upper()}\n{'='*60}")
        print(f"💰 Remaining Budget: ${self.travel_plan.remaining_budget:.2f} | 📅 {nights} nights\n")
        print(hotel_suggestions)
        
        # Booking interaction
        while True:
            choice = self.get_text_input("\nChoose an option (1-3) or [X] to go back: ").upper()
            
            if choice == 'X':
                return
                
            if choice in ('1', '2', '3'):
                price = self.get_numeric_input(f"Confirm price for Option {choice}: $", min_value=0)
                
                if price <= self.travel_plan.remaining_budget:
                    self.travel_plan.hotels = {
                        'option': int(choice),
                        'price': price,
                        'nights': nights
                    }
                    self.travel_plan.remaining_budget -= price
                    print(f"\n✅ Hotel option {choice} booked! Remaining budget: ${self.travel_plan.remaining_budget:.2f}")
                    return
                else:
                    print("⚠️ Price exceeds budget!")
            else:
                print("Please enter a valid option (1-3) or X to go back.")

    def discuss_activities(self) -> None:
        """Interactive activity search and booking."""
        self.display_header("ACTIVITY SEARCH")
        
        if not self.travel_plan.hotels:
            print("\n🏨 Please book hotels first!")
            return
            
        # Initialize activities list if needed
        if self.travel_plan.activities is None:
            self.travel_plan.activities = []
            
        # If activity service exists, use its conversational interface
        if self.activity_service:
            # Use the activity service's discuss_activities method which has conversation capabilities
            self.activity_service.discuss_activities(self.travel_plan)
            return
        
        # Otherwise fall back to basic functionality
        # Calculate stay duration
        departure_date_obj = datetime.strptime(self.travel_plan.departure_date, "%Y-%m-%d")
        return_date_obj = datetime.strptime(self.travel_plan.return_date, "%Y-%m-%d")
        days = (return_date_obj - departure_date_obj).days
        
        # Fall back to the API wrappers
        activity_suggestions = get_activity_suggestions(
            self.travel_plan.destination['name'],
            self.travel_plan.remaining_budget,
            days
        )
        
        print(f"\n{'='*60}\n🎭 ACTIVITY SUGGESTIONS IN {self.travel_plan.destination['name'].upper()}\n{'='*60}")
        print(f"💰 Remaining Budget: ${self.travel_plan.remaining_budget:.2f} | 📅 {days} days\n")
        print(activity_suggestions)
        
        # Booking interaction
        while True:
            choice = self.get_text_input("\nChoose an option (1-5) or [X] to go back, [D] when done: ").upper()
            
            if choice == 'X':
                return
                
            if choice == 'D':
                print("✅ Activities selection complete!")
                return
                
            if choice in ('1', '2', '3', '4', '5'):
                price = self.get_numeric_input(
                    f"Enter price for Activity {choice} (per person): $", 
                    min_value=0
                )
                
                total_price = price * self.travel_plan.travelers
                
                if total_price <= self.travel_plan.remaining_budget:
                    # Add to activities list
                    self.travel_plan.activities.append({
                        'option': int(choice),
                        'price': total_price
                    })
                    self.travel_plan.remaining_budget -= total_price
                    print(f"\n✅ Activity {choice} booked! Remaining budget: ${self.travel_plan.remaining_budget:.2f}")
                    
                    # Ask to book more
                    if self.travel_plan.remaining_budget > 0:
                        more = self.get_text_input("Book another activity? (y/n): ").lower()
                        if more != 'y':
                            return
                    else:
                        print("⚠️ Budget fully allocated!")
                        return
                else:
                    print("⚠️ Price exceeds remaining budget!")
            else:
                print("Please enter a valid option (1-5), X to go back, or D when done.")

    def display_full_itinerary(self) -> None:
        """Display the complete travel itinerary."""
        self.display_header("FULL TRAVEL ITINERARY")
        
        print("\n┌─────────────── YOUR JOURNEY ───────────────┐")
        print(f"│  🌍 Destination: {self.travel_plan.destination['name']}".ljust(50) + "│")
        print(f"│  📅 From {self.travel_plan.departure_date} to {self.travel_plan.return_date}".ljust(50) + "│")
        print(f"│  👥 Travelers: {self.travel_plan.travelers}".ljust(50) + "│")
        print("└───────────────────────────────────────────┘")
        
        # Calculate total spent
        flight_cost = self.travel_plan.flights.get('price', 0) if self.travel_plan.flights else 0
        hotel_cost = self.travel_plan.hotels.get('price', 0) if self.travel_plan.hotels else 0
        activity_cost = sum(act.get('price', 0) for act in self.travel_plan.activities) if self.travel_plan.activities else 0
        total_spent = flight_cost + hotel_cost + activity_cost
        
        # Budget summary with percentage
        percent_used = (total_spent / self.travel_plan.total_budget) * 100 if self.travel_plan.total_budget > 0 else 0
        
        print("\n┌─────────────── BUDGET SUMMARY ───────────────┐")
        print(f"│  💰 Total Budget:    ${self.travel_plan.total_budget:.2f}".ljust(50) + "│")
        print(f"│  💸 Total Spent:     ${total_spent:.2f} ({percent_used:.1f}% of budget)".ljust(50) + "│")
        print(f"│  💵 Remaining Budget: ${self.travel_plan.remaining_budget:.2f}".ljust(50) + "│")
        print("└─────────────────────────────────────────────┘")
        
        # Flight details
        if self.travel_plan.flights:
            print("\n┌─────────────── ✈️ FLIGHT DETAILS ───────────────┐")
            print(f"│  🎫 Selected:  Option {self.travel_plan.flights['option']}".ljust(50) + "│")
            print(f"│  💲 Price:     ${self.travel_plan.flights['price']:.2f}".ljust(50) + "│")
            
            # Display compact version of flight details
            flight_info = self.travel_plan.flights.get('details', '')
            if isinstance(flight_info, str):
                lines = flight_info.split('\n')
                
                # Filter important lines from the flight details
                option_num = self.travel_plan.flights['option']
                in_selected_option = False
                selected_details = []
                
                for line in lines:
                    if f"[OPTION {option_num}]" in line:
                        in_selected_option = True
                    elif in_selected_option and line.startswith("=====") and "OPTION" in line:
                        in_selected_option = False
                    
                    if in_selected_option and (
                        "Price:" in line or 
                        "OUTBOUND" in line or 
                        "RETURN" in line or
                        line.strip().startswith("•")
                    ):
                        selected_details.append(line)
                
                print("└─────────────────────────────────────────────┘")
                if selected_details:
                    print("\n📋 FLIGHT ROUTE DETAILS:")
                    print("─────────────────────────────────────────────")
                    for detail in selected_details:
                        print(f"  {detail}")
            else:
                # Just display basic flight info
                print(f"│  🛫 From:      {self.travel_plan.departure['name']} ({self.travel_plan.departure['iata']})".ljust(50) + "│")
                print(f"│  🛬 To:        {self.travel_plan.destination['name']} ({self.travel_plan.destination['iata']})".ljust(50) + "│")
                print(f"│  📅 Depart:    {self.travel_plan.departure_date}".ljust(50) + "│")
                print(f"│  📅 Return:    {self.travel_plan.return_date}".ljust(50) + "│")
                print("└─────────────────────────────────────────────┘")
        else:
            print("\n⚠️ No flights booked - You should book flights first! ⚠️")
        
        # Hotel details
        if self.travel_plan.hotels:
            print("\n┌─────────────── 🏨 HOTEL DETAILS ───────────────┐")
            print(f"│  🎫 Selected:  Option {self.travel_plan.hotels['option']}".ljust(50) + "│")
            print(f"│  💲 Price:     ${self.travel_plan.hotels['price']:.2f}".ljust(50) + "│")
            print(f"│  📆 Duration:  {self.travel_plan.hotels['nights']} nights".ljust(50) + "│")
            print("└─────────────────────────────────────────────┘")
        else:
            print("\n⚠️ No accommodation booked - You should book a hotel! ⚠️")
        
        # Activity details
        if self.travel_plan.activities:
            total_activities_cost = sum(act.get('price', 0) for act in self.travel_plan.activities)
            
            print("\n┌─────────────── 🎭 ACTIVITIES ───────────────┐")
            print(f"│  🎯 Total Activities: {len(self.travel_plan.activities)}".ljust(50) + "│")
            print(f"│  💲 Total Cost:      ${total_activities_cost:.2f}".ljust(50) + "│")
            print("└─────────────────────────────────────────────┘")
            
            print("\n📋 BOOKED ACTIVITIES:")
            print("─────────────────────────────────────────────")
            for i, activity in enumerate(self.travel_plan.activities, 1):
                activity_name = activity.get('name', f"Activity option {activity['option']}")
                activity_category = activity.get('category', 'General')
                print(f"  {i}. {activity_name} - ${activity['price']:.2f}")
                if 'category' in activity:
                    print(f"     Category: {activity_category}")
                if 'duration' in activity:
                    print(f"     Duration: {activity['duration']}")
                print()
        else:
            print("\n⚠️ No activities booked - Add some fun to your trip! ⚠️")
        
        # Final budget summary
        if total_spent > 0:
            print("\n┌─────────────── 📊 EXPENSE BREAKDOWN ───────────────┐")
            if flight_cost > 0:
                flight_percent = (flight_cost/total_spent)*100
                print(f"│  ✈️  Flights:        ${flight_cost:.2f} ({flight_percent:.1f}%)".ljust(50) + "│")
            if hotel_cost > 0:
                hotel_percent = (hotel_cost/total_spent)*100
                print(f"│  🏨 Accommodation:  ${hotel_cost:.2f} ({hotel_percent:.1f}%)".ljust(50) + "│")
            if activity_cost > 0:
                activity_percent = (activity_cost/total_spent)*100
                print(f"│  🎭 Activities:     ${activity_cost:.2f} ({activity_percent:.1f}%)".ljust(50) + "│")
            print("│".ljust(50) + "│")
            print(f"│  💰 Total Spent:     ${total_spent:.2f}".ljust(50) + "│")
            print(f"│  💵 Remaining:       ${self.travel_plan.remaining_budget:.2f}".ljust(50) + "│")
            print("└─────────────────────────────────────────────┘")
        
        # Wait for user to continue
        input("\n✨ Press Enter to continue... ✨")

    def save_itinerary(self) -> None:
        """Save the itinerary to a file."""
        self.display_header("SAVE ITINERARY")
        
        filename = self.get_text_input("Enter filename to save (default: itinerary.txt): ")
        if not filename:
            filename = "itinerary.txt"
            
        # Make sure the filename has .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # Calculate total spent
        flight_cost = self.travel_plan.flights.get('price', 0) if self.travel_plan.flights else 0
        hotel_cost = self.travel_plan.hotels.get('price', 0) if self.travel_plan.hotels else 0
        activity_cost = sum(act.get('price', 0) for act in self.travel_plan.activities) if self.travel_plan.activities else 0
        total_spent = flight_cost + hotel_cost + activity_cost
        
        # Budget percentage
        percent_used = (total_spent / self.travel_plan.total_budget) * 100 if self.travel_plan.total_budget > 0 else 0
            
        try:
            with open(filename, 'w') as file:
                # Write header
                file.write(f"{'='*60}\n")
                file.write(f"TRAVEL ITINERARY\n")
                file.write(f"{'='*60}\n\n")
                
                # Basic trip details
                file.write(f"Trip to {self.travel_plan.destination['name']}\n")
                file.write(f"From {self.travel_plan.departure_date} to {self.travel_plan.return_date}\n")
                file.write(f"Travelers: {self.travel_plan.travelers}\n\n")
                
                # Budget summary
                file.write(f"{'='*60}\n")
                file.write(f"BUDGET SUMMARY\n")
                file.write(f"{'='*60}\n\n")
                file.write(f"Total Budget: ${self.travel_plan.total_budget:.2f}\n")
                file.write(f"Total Spent: ${total_spent:.2f} ({percent_used:.1f}% of budget)\n")
                file.write(f"Remaining Budget: ${self.travel_plan.remaining_budget:.2f}\n")
                
                # Flight details
                if self.travel_plan.flights:
                    file.write(f"\n{'='*60}\n")
                    file.write(f"FLIGHT DETAILS\n")
                    file.write(f"{'='*60}\n\n")
                    file.write(f"Price: ${self.travel_plan.flights['price']:.2f}\n\n")
                    
                    # Write selected flight details
                    flight_info = self.travel_plan.flights.get('details', '')
                    option_num = self.travel_plan.flights['option']
                    
                    # Check if flight_info is a string
                    if isinstance(flight_info, str):
                        # Extract relevant parts of the flight details
                        lines = flight_info.split('\n')
                        in_selected_option = False
                        for line in lines:
                            if f"[OPTION {option_num}]" in line:
                                in_selected_option = True
                                file.write("SELECTED FLIGHT:\n")
                            elif in_selected_option and line.startswith("=====") and "OPTION" in line:
                                in_selected_option = False
                            
                            if in_selected_option and "OPTION" not in line:
                                file.write(f"{line}\n")
                    else:
                        # Just write a basic summary
                        file.write(f"Selected flight option {option_num}\n")
                        file.write(f"From: {self.travel_plan.departure['name']} ({self.travel_plan.departure['iata']})\n")
                        file.write(f"To: {self.travel_plan.destination['name']} ({self.travel_plan.destination['iata']})\n")
                        file.write(f"Departure: {self.travel_plan.departure_date}\n")
                        file.write(f"Return: {self.travel_plan.return_date}\n")
                
                # Hotel details
                if self.travel_plan.hotels:
                    file.write(f"\n{'='*60}\n")
                    file.write(f"ACCOMMODATION DETAILS\n")
                    file.write(f"{'='*60}\n\n")
                    file.write(f"Option {self.travel_plan.hotels['option']}\n")
                    file.write(f"Price: ${self.travel_plan.hotels['price']:.2f}\n")
                    file.write(f"Duration: {self.travel_plan.hotels['nights']} nights\n")
                
                # Activity details
                if self.travel_plan.activities:
                    file.write(f"\n{'='*60}\n")
                    file.write(f"ACTIVITIES\n")
                    file.write(f"{'='*60}\n\n")
                    
                    total_activities_cost = sum(act.get('price', 0) for act in self.travel_plan.activities)
                    file.write(f"Total activities cost: ${total_activities_cost:.2f}\n\n")
                    
                    for i, activity in enumerate(self.travel_plan.activities, 1):
                        activity_name = activity.get('name', f"Activity option {activity['option']}")
                        file.write(f"{i}. {activity_name} - ${activity['price']:.2f}\n")
                
                # Expense breakdown
                file.write(f"\n{'='*60}\n")
                file.write(f"EXPENSE BREAKDOWN\n")
                file.write(f"{'='*60}\n\n")
                
                if total_spent > 0:
                    file.write(f"Flights: ${flight_cost:.2f} ({(flight_cost/total_spent)*100:.1f}% of total)\n")
                    file.write(f"Accommodation: ${hotel_cost:.2f} ({(hotel_cost/total_spent)*100:.1f}% of total)\n")
                    file.write(f"Activities: ${activity_cost:.2f} ({(activity_cost/total_spent)*100:.1f}% of total)\n")
                    file.write(f"Total Spent: ${total_spent:.2f}\n")
                    file.write(f"Remaining: ${self.travel_plan.remaining_budget:.2f}\n")
                
                # Footer
                file.write(f"\n{'='*60}\n")
                file.write(f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}\n")
                file.write(f"{'='*60}\n")
                
            print(f"\n✅ Itinerary saved to {filename}")
        except Exception as e:
            print(f"\n❌ Error saving itinerary: {e}")
            
        input("\nPress Enter to continue...")

def run_cli():
    """Run the CLI application."""
    from models.travel_plan import TravelPlan
    from services.flight_service import FlightService
    from services.hotel_service import HotelService
    from services.activity_service import ActivityService
    from langchain_openai import OpenAI
    from config import load_api_keys
    
    # Load API keys
    keys = load_api_keys()
    
    # Initialize LLM
    llm = OpenAI(openai_api_key=keys['openai_api_key'], temperature=0.7)
    
    # Initialize services
    flight_service = FlightService(
        amadeus_client_id=keys['amadeus_client_id'],
        amadeus_client_secret=keys['amadeus_client_secret'],
        google_maps_key=keys['google_maps_key'],
        llm=llm
    )
    
    hotel_service = HotelService(llm=llm)
    activity_service = ActivityService(llm=llm)
    
    # Create travel plan
    travel_plan = TravelPlan()
    
    # Initialize CLI with services
    cli = TravelPlannerCLI(
        travel_plan=travel_plan,
        flight_service=flight_service,
        hotel_service=hotel_service,
        activity_service=activity_service
    )
    
    try:
        cli.collect_initial_details()
        cli.show_main_menu()
    except KeyboardInterrupt:
        print("\n\nExiting Travel Planner. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_cli()