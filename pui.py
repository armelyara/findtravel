import streamlit as st
from datetime import datetime
from models.travel_plan import TravelPlan
from services.api_wrappers import search_flights, format_flight_data, get_hotel_suggestions, get_activity_suggestions
from utils.location_utils import find_iata_code
from utils.date_utils import validate_date_format

# Initialize session state
if 'travel_plan' not in st.session_state:
    st.session_state.travel_plan = TravelPlan()
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Welcome to the Travel Planning Assistant! Where would you like to go on your next trip?"}
    ]
    st.session_state.current_step = "destination"
    st.session_state.pending_action = None

class IntegratedTravelAgent:
    def __init__(self):
        """Initialize the agent"""
        pass  # All initialization is now handled above

    def display_conversation(self):
        """Display the chat interface"""
        with st.container():
            for message in st.session_state.get('messages', []):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # Show budget if available
                    if (message["role"] == "assistant" and 
                        hasattr(st.session_state.travel_plan, 'total_budget') and 
                        hasattr(st.session_state.travel_plan, 'remaining_budget')):
                        remaining = st.session_state.travel_plan.remaining_budget or 0  # Handle None
                        total = st.session_state.travel_plan.total_budget or 0  # Handle None
                        
                        # Only show progress bar if both values are valid
                        if total > 0:
                            st.progress(remaining/total)
                            st.caption(f"Budget: ${remaining:.2f} remaining of ${total:.2f}")

    def display_sidebar(self):
        """Display the right sidebar with trip details"""
        with st.sidebar:
            st.header("Trip Overview")
            
            # Safe attribute checking
            travel_plan = st.session_state.get('travel_plan', None)
            
            if travel_plan:
                st.subheader("Trip")
                if hasattr(travel_plan, 'departure'):
                    st.write(f"🛫 From: {travel_plan.departure.get('name', 'Not set')}")
                
                if hasattr(travel_plan, 'destination'):
                    st.write(f"🛬 To: {travel_plan.destination.get('name', 'Not set')}")
            
            if travel_plan and hasattr(travel_plan, 'departure_date'):
                st.subheader("Dates")
                st.write(f"📅 {travel_plan.departure_date} to {travel_plan.return_date}")
            
            if travel_plan and hasattr(travel_plan, 'total_budget'):
                # Get values with proper defaults
                remaining = getattr(travel_plan, 'remaining_budget', 0) or 0  # Handle None values
                total = getattr(travel_plan, 'total_budget', 0) or 0  # Handle None values
                
                st.subheader("Budget")
                st.metric("Remaining", f"${remaining:.2f}", f"${remaining-total:.2f}")
                
                # Breakdown with safe attribute access
                flight_cost = travel_plan.flights.get('price', 0) if hasattr(travel_plan, 'flights') and travel_plan.flights else 0
                hotel_cost = travel_plan.hotels.get('price', 0) if hasattr(travel_plan, 'hotels') and travel_plan.hotels else 0
                activity_cost = sum(a.get('price', 0) for a in travel_plan.activities) if hasattr(travel_plan, 'activities') else 0
                
                st.write("**Breakdown:**")
                st.write(f"✈️ Flights: ${flight_cost:.2f}")
                st.write(f"🏨 Hotels: ${hotel_cost:.2f}")
                st.write(f"🎭 Activities: ${activity_cost:.2f}")
            else:
                st.warning("Budget information not available")

    def add_message(self, role, content):
        """Add a message to the conversation"""
        st.session_state.messages.append({"role": role, "content": content})

    def process_input(self, user_input):
        """Process user input using your actual backend logic"""
        self.add_message("user", user_input)
        
        try:
            if st.session_state.current_step == "destination":
                self._process_destination(user_input)
            elif st.session_state.current_step == "departure":
                self._process_departure(user_input)
            elif st.session_state.current_step == "dates":
                self._process_dates(user_input)
            elif st.session_state.current_step == "travelers":
                self._process_travelers(user_input)
            elif st.session_state.current_step == "budget":
                self._process_budget(user_input)
            elif st.session_state.current_step == "flights":
                self._process_flights(user_input)
            elif st.session_state.current_step == "hotels":
                self._process_hotels(user_input)
            elif st.session_state.current_step == "activities":
                self._process_activities(user_input)
            elif st.session_state.current_step == "summary":
                self._process_summary(user_input)
            
            # Force immediate rerun to process the next step if needed
            st.rerun()
            
        except Exception as e:
            self.add_message("assistant", f"Sorry, something went wrong: {str(e)}")
            st.error(f"Error: {str(e)}")

    def _process_destination(self, user_input):
        """Process destination using your actual location_utils"""
        result = find_iata_code(user_input)
        if result:
            st.session_state.travel_plan.destination = result
            self.add_message("assistant", f"Great choice! {result['name']} is amazing. Where will you be departing from?")
            st.session_state.current_step = "departure"
        else:
            self.add_message("assistant", "I couldn't find that destination. Try being more specific (e.g., 'Paris, France')")
    
    def _process_departure(self, user_input):
        """Process departure location using your actual location_utils"""
        result = find_iata_code(user_input)
        if result:
            st.session_state.travel_plan.departure = result
            self.add_message("assistant", f"Perfect! You'll depart from {result['name']}. When would you like to travel? (YYYY-MM-DD to YYYY-MM-DD)")
            st.session_state.current_step = "dates"
        else:
            self.add_message("assistant", "I couldn't find that departure location. Try being more specific (e.g., 'New York, USA')")

    def _process_dates(self, user_input):
        """Process dates using your date_utils"""
        try:
            date_range = [d.strip() for d in user_input.split("to")]
            if len(date_range) == 2 and all(validate_date_format(d) for d in date_range):
                st.session_state.travel_plan.departure_date = date_range[0]
                st.session_state.travel_plan.return_date = date_range[1]
                self.add_message("assistant", f"Got it! How many people are traveling?")
                st.session_state.current_step = "travelers"
            else:
                self.add_message("assistant", "Please enter dates in format: YYYY-MM-DD to YYYY-MM-DD")
        except Exception as e:
            self.add_message("assistant", f"Date error: {str(e)}")

    def _process_travelers(self, user_input):
        """Process travelers input"""
        try:
            travelers = int(user_input)
            if travelers > 0:
                st.session_state.travel_plan.travelers = travelers
                self.add_message("assistant", f"Perfect! What's your total budget for this trip? (e.g., 2000)")
                st.session_state.current_step = "budget"
            else:
                self.add_message("assistant", "Please enter a positive number")
        except ValueError:
            self.add_message("assistant", "Please enter a valid number")

    def _process_budget(self, user_input):
        """Process budget input"""
        try:
            budget = float(user_input)
            if budget > 0:
                st.session_state.travel_plan.total_budget = budget
                st.session_state.travel_plan.remaining_budget = budget
                self.add_message("assistant", f"Budget set! Would you like to search for flights now? (yes/no)")
                st.session_state.current_step = "flights"
            else:
                self.add_message("assistant", "Please enter a positive amount")
        except ValueError:
            self.add_message("assistant", "Please enter a valid number")

    def _process_flights(self, user_input):
        """Process flights using your actual flight service"""
        if user_input.lower() == 'yes':
            with st.spinner("Searching flights..."):
                flights = search_flights(
                    st.session_state.travel_plan.departure['iata'],
                    st.session_state.travel_plan.destination['iata'],
                    st.session_state.travel_plan.departure_date,
                    st.session_state.travel_plan.return_date,
                    st.session_state.travel_plan.travelers,
                    st.session_state.travel_plan.remaining_budget
                )
                formatted = format_flight_data(flights, st.session_state.travel_plan)
                self.add_message("assistant", formatted)
                self.add_message("assistant", "Please select an option (1-3) or type 'skip'")
                st.session_state.pending_action = "book_flight"
        elif user_input.lower() == 'no':
            self.add_message("assistant", "Would you like to search for hotels instead?")
            st.session_state.current_step = "hotels"
        elif st.session_state.pending_action == "book_flight":
            self._book_flight(user_input)

    def _book_flight(self, user_input):
        """Book flight using your actual flight data"""
        if user_input.isdigit() and int(user_input) in [1, 2, 3]:
            option = int(user_input) - 1
            flights = search_flights(
                st.session_state.travel_plan.departure['iata'],
                st.session_state.travel_plan.destination['iata'],
                st.session_state.travel_plan.departure_date,
                st.session_state.travel_plan.return_date,
                st.session_state.travel_plan.travelers,
                st.session_state.travel_plan.remaining_budget
            )
            price = float(flights['data'][option]['price']['total'])
            
            if price <= st.session_state.travel_plan.remaining_budget:
                st.session_state.travel_plan.flights = {
                    'option': int(user_input),
                    'price': price,
                    'details': format_flight_data(flights, st.session_state.travel_plan)
                }
                st.session_state.travel_plan.remaining_budget -= price
                self.add_message("assistant", f"Flight booked! Remaining budget: ${st.session_state.travel_plan.remaining_budget:.2f}. Search for hotels? (yes/no)")
                st.session_state.current_step = "hotels"
                st.session_state.pending_action = None
            else:
                self.add_message("assistant", f"That exceeds your budget by ${price - st.session_state.travel_plan.remaining_budget:.2f}. Please choose another option.")
        elif user_input.lower() == 'skip':
            self.add_message("assistant", "Skipping flights. Search for hotels? (yes/no)")
            st.session_state.current_step = "hotels"
            st.session_state.pending_action = None
        else:
            self.add_message("assistant", "Please select 1-3 or type 'skip'")

    def _process_hotels(self, user_input):
        """Process hotels using your actual hotel service"""
        if user_input.lower() == 'yes':
            with st.spinner("Searching hotels..."):
                nights = (datetime.strptime(st.session_state.travel_plan.return_date, "%Y-%m-%d") - 
                         datetime.strptime(st.session_state.travel_plan.departure_date, "%Y-%m-%d")).days
                hotels = get_hotel_suggestions(
                    st.session_state.travel_plan.destination['name'],
                    st.session_state.travel_plan.remaining_budget,
                    nights,
                    st.session_state.travel_plan.travelers
                )
                self.add_message("assistant", hotels)
                self.add_message("assistant", "Please select an option (1-3) or type 'skip'")
                st.session_state.pending_action = "book_hotel"
        elif user_input.lower() == 'no':
            self.add_message("assistant", "Would you like to search for activities instead?")
            st.session_state.current_step = "activities"
        elif st.session_state.pending_action == "book_hotel":
            self._book_hotel(user_input)

    def _book_hotel(self, user_input):
        """Book hotel using your actual hotel data"""
        if user_input.isdigit() and int(user_input) in [1, 2, 3]:
            # This is a simplified booking - you would use your actual hotel booking logic
            nights = (datetime.strptime(st.session_state.travel_plan.return_date, "%Y-%m-%d") - 
                     datetime.strptime(st.session_state.travel_plan.departure_date, "%Y-%m-%d")).days
            price = 100 * int(user_input) * nights  # Simplified pricing
            
            if price <= st.session_state.travel_plan.remaining_budget:
                st.session_state.travel_plan.hotels = {
                    'option': int(user_input),
                    'price': price,
                    'nights': nights
                }
                st.session_state.travel_plan.remaining_budget -= price
                self.add_message("assistant", f"Hotel booked! Remaining budget: ${st.session_state.travel_plan.remaining_budget:.2f}. Search for activities? (yes/no)")
                st.session_state.current_step = "activities"
                st.session_state.pending_action = None
            else:
                self.add_message("assistant", f"That exceeds your budget by ${price - st.session_state.travel_plan.remaining_budget:.2f}. Please choose another option.")
        elif user_input.lower() == 'skip':
            self.add_message("assistant", "Skipping hotels. Search for activities? (yes/no)")
            st.session_state.current_step = "activities"
            st.session_state.pending_action = None
        else:
            self.add_message("assistant", "Please select 1-3 or type 'skip'")

    def _process_activities(self, user_input):
        """Process activities using your actual activity service"""
        if user_input.lower() == 'yes':
            with st.spinner("Searching activities..."):
                days = (datetime.strptime(st.session_state.travel_plan.return_date, "%Y-%m-%d") - 
                       datetime.strptime(st.session_state.travel_plan.departure_date, "%Y-%m-%d")).days
                activities = get_activity_suggestions(
                    st.session_state.travel_plan.destination['name'],
                    st.session_state.travel_plan.remaining_budget,
                    days
                )
                self.add_message("assistant", activities)
                self.add_message("assistant", "Select activities to add (comma-separated numbers) or type 'done'")
                st.session_state.pending_action = "add_activities"
        elif user_input.lower() == 'no':
            self.add_message("assistant", "Type 'summary' to see your complete itinerary")
            st.session_state.current_step = "summary"
        elif st.session_state.pending_action == "add_activities":
            self._add_activities(user_input)

    def _add_activities(self, user_input):
        """Add activities using your actual activity data"""
        if user_input.lower() == 'done':
            self.add_message("assistant", "Type 'summary' to see your complete itinerary")
            st.session_state.current_step = "summary"
            st.session_state.pending_action = None
        else:
            try:
                selected = [int(num.strip()) for num in user_input.split(",")]
                days = (datetime.strptime(st.session_state.travel_plan.return_date, "%Y-%m-%d") - 
                       datetime.strptime(st.session_state.travel_plan.departure_date, "%Y-%m-%d")).days
                activities = get_activity_suggestions(
                    st.session_state.travel_plan.destination['name'],
                    st.session_state.travel_plan.remaining_budget,
                    days
                )
                
                # Simplified activity addition - adapt with your actual logic
                total_cost = 0
                for num in selected:
                    if 1 <= num <= 5:  # Assuming 5 activity options
                        price = 50 * num  # Simplified pricing
                        total_cost += price
                
                if total_cost <= st.session_state.travel_plan.remaining_budget:
                    if not hasattr(st.session_state.travel_plan, 'activities'):
                        st.session_state.travel_plan.activities = []
                    
                    for num in selected:
                        st.session_state.travel_plan.activities.append({
                            'option': num,
                            'price': 50 * num
                        })
                    
                    st.session_state.travel_plan.remaining_budget -= total_cost
                    self.add_message("assistant", f"Added {len(selected)} activities! Remaining budget: ${st.session_state.travel_plan.remaining_budget:.2f}. Add more or type 'done'")
                else:
                    self.add_message("assistant", f"Those activities exceed your budget by ${total_cost - st.session_state.travel_plan.remaining_budget:.2f}. Please select fewer options.")
            except ValueError:
                self.add_message("assistant", "Please enter numbers separated by commas (e.g., '1,3') or type 'done'")

    def _process_summary(self, user_input):
        """Generate summary using your actual travel plan data"""
        if "summary" in user_input.lower():
            flight_cost = st.session_state.travel_plan.flights.get('price', 0) if hasattr(st.session_state.travel_plan, 'flights') else 0
            hotel_cost = st.session_state.travel_plan.hotels.get('price', 0) if hasattr(st.session_state.travel_plan, 'hotels') else 0
            activity_cost = sum(a.get('price', 0) for a in st.session_state.travel_plan.activities) if hasattr(st.session_state.travel_plan, 'activities') else 0
            
            summary = f"""
            **Trip Summary**
            From: {st.session_state.travel_plan.departure['name'] if hasattr(st.session_state.travel_plan, 'departure') else 'Not set'} 
            To: {st.session_state.travel_plan.destination['name']}
            Dates: {st.session_state.travel_plan.departure_date} to {st.session_state.travel_plan.return_date}
            Travelers: {st.session_state.travel_plan.travelers}
            
            **Budget**
            Total: ${st.session_state.travel_plan.total_budget:.2f}
            Spent: ${flight_cost + hotel_cost + activity_cost:.2f}
            Remaining: ${st.session_state.travel_plan.remaining_budget:.2f}
            
            **Bookings**
            Flights: {'Not booked' if flight_cost == 0 else f"Option {st.session_state.travel_plan.flights['option']} (${flight_cost:.2f})"}
            Hotels: {'Not booked' if hotel_cost == 0 else f"Option {st.session_state.travel_plan.hotels['option']} (${hotel_cost:.2f})"}
            Activities: {len(st.session_state.travel_plan.activities) if hasattr(st.session_state.travel_plan, 'activities') else 0} (${activity_cost:.2f})
            """
            
            self.add_message("assistant", summary)
            self.add_message("assistant", "Type 'restart' to plan a new trip or 'save' to save this itinerary")

    def run(self):
        """Run the application"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.header("Travel Planning Assistant")
            self.display_conversation()
            
            if prompt := st.chat_input("Type your message..."):
                self.process_input(prompt)
        
        with col2:
            self.display_sidebar()

if __name__ == "__main__":
    agent = IntegratedTravelAgent()
    agent.run()