"""
Hotel service for managing hotel-related operations
"""
from typing import Dict, Any
from datetime import datetime
from models.travel_plan import TravelPlan
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from utils.input_utils import get_numeric_input

class HotelService:
    """Service for hotel search and booking"""
    
    def __init__(self, llm: Any):
        self.llm = llm
        
    def discuss_hotels(self, travel_plan: TravelPlan) -> None:
        """AI-generated hotel suggestions without hardcoded data"""
        if not travel_plan.flights:
            print("\n✈️ Please book flights first!")
            return
        # Calculate stay duration
        nights = travel_plan.get_trip_duration_days()
        max_per_night = travel_plan.remaining_budget / nights if nights > 0 else travel_plan.remaining_budget
        # AI Prompt Template
        prompt = PromptTemplate(
            input_variables=["destination", "budget", "nights"],
            template="""As a travel assistant, suggest 3 hotel options in {destination} for a {nights}-night stay
            with a total budget of ${budget:.2f}. For each option include:
            - Hotel name (make it realistic for the city)
            - Star rating (3-5 stars)
            - Location area
            - Breakfast inclusion
            - Approximate total price (should be under ${budget:.2f})
            - Brief selling point
            Format as a numbered list with clear sections."""
        )
        # Generate suggestions
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.invoke({
            "destination": travel_plan.destination['name'],
            "budget": travel_plan.remaining_budget,
            "nights": nights
        })["text"]
        # Display results
        print(f"\n{'='*60}\n🏨 RECOMMENDED HOTELS IN {travel_plan.destination['name'].upper()}\n{'='*60}")
        print(f"💰 Remaining Budget: ${travel_plan.remaining_budget:.2f} | 📅 {nights} nights\n")
        print(response)
        
        # Use a direct prompt template approach instead of chains with memory
        inquiry_template = """You're a helpful hotel booking assistant for {destination}.
        The user has a budget of ${budget:.2f} for a {nights}-night stay.
        
        Available hotel options:
        {hotels_info}
        
        The user's question is: {question}
        
        Please provide a detailed and helpful response about the hotel options specifically addressing the user's question."""
        
        # Booking interaction
        while True:
            choice = input("\nChoose an option (1-3) or [X] to skip, or ask a question about the options: ").strip().upper()
            
            if choice == 'X':
                return
                
            if choice in ('1', '2', '3'):
                # Extract hotel info from the response to avoid asking user for redundant information
                option_num = int(choice)
                
                # Parse response to get price - simplified approach using estimated prices
                estimated_prices = {
                    1: min(travel_plan.remaining_budget * 0.4, 200 * nights),  # Option 1 - premium 
                    2: min(travel_plan.remaining_budget * 0.3, 150 * nights),  # Option 2 - mid-range
                    3: min(travel_plan.remaining_budget * 0.2, 100 * nights)   # Option 3 - budget
                }
                price = estimated_prices[option_num]
                
                # Confirm booking with extracted information
                print(f"\nHotel Option {choice} - Estimated price: ${price:.2f} for {nights} nights")
                confirm = input("Confirm booking? (y/n): ").lower()
                
                if confirm == 'y':
                    if price <= travel_plan.remaining_budget:
                        travel_plan.hotels = {
                            'option': option_num,
                            'price': price,
                            'nights': nights,
                            'destination': travel_plan.destination['name']
                        }
                        travel_plan.remaining_budget -= price
                        print(f"✅ Hotel choice {choice} booked! Remaining budget: ${travel_plan.remaining_budget:.2f}")
                        return
                    else:
                        print(f"⚠️ Price ${price:.2f} exceeds your remaining budget of ${travel_plan.remaining_budget:.2f}!")
                else:
                    print("Booking cancelled. You can select another option.")
            else:
                # Use direct prompt instead of chain with memory
                filled_prompt = inquiry_template.format(
                    destination=travel_plan.destination['name'],
                    budget=travel_plan.remaining_budget,
                    nights=nights,
                    hotels_info=response,
                    question=choice
                )
                # Call the LLM directly with correct output handling
                response = str(self.llm.invoke(filled_prompt))
                print(f"\nAssistant: {response}")
    
    def get_hotel_summary(self, travel_plan: TravelPlan) -> str:
        """Return a summary of booked hotel information"""
        if not travel_plan.hotels:
            return "No hotel booked yet."
            
        return f"""🏨 HOTEL BOOKING SUMMARY
Destination: {travel_plan.hotels.get('destination', travel_plan.destination['name'])}
Option: {travel_plan.hotels.get('option')}
Nights: {travel_plan.hotels.get('nights')}
Total Price: ${travel_plan.hotels.get('price', 0):.2f}"""
    
    def get_hotel_suggestions(self, destination, budget, nights):
        """Get hotel suggestions and return data instead of printing."""
        max_per_night = budget / nights if nights > 0 else budget
        
        # Generate suggestions using the LLM
        prompt = f"""As a travel assistant, suggest 3 hotel options in {destination} for a {nights}-night stay
        with a total budget of ${budget:.2f}. For each option include:
        - Hotel name (make it realistic for the city)
        - Star rating (3-5 stars)
        - Location area
        - Breakfast inclusion
        - Approximate total price (should be under ${budget:.2f})
        - Brief selling point
        
        Format as a structured list with clear sections."""
        
        response = self.llm.invoke(prompt)
        
        # Parse the response into a structured format
        hotel_options = []
        current_option = {}
        
        for line in str(response).split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('1.') or line.startswith('Option 1:'):
                current_option = {'option': 1}
                hotel_options.append(current_option)
            elif line.startswith('2.') or line.startswith('Option 2:'):
                current_option = {'option': 2}
                hotel_options.append(current_option)
            elif line.startswith('3.') or line.startswith('Option 3:'):
                current_option = {'option': 3}
                hotel_options.append(current_option)
            
            # Parse hotel details
            if 'option' in current_option:
                if 'name' not in current_option and ':' not in line and len(line) > 5:
                    current_option['name'] = line
                elif 'star' in line.lower() or '⭐' in line:
                    current_option['stars'] = line
                elif 'location' in line.lower() or 'area' in line.lower():
                    current_option['location'] = line.split(':')[-1].strip()
                elif 'breakfast' in line.lower():
                    current_option['breakfast'] = line.split(':')[-1].strip()
                elif 'price' in line.lower() or '$' in line:
                    try:
                        price_text = line.split('$')[1].split()[0].replace(',', '')
                        current_option['price'] = float(price_text)
                    except:
                        # Estimate a price if parsing fails
                        current_option['price'] = budget * (0.7 if current_option['option'] == 3 else 
                                                          0.8 if current_option['option'] == 2 else 0.9)
                elif 'feature' in line.lower() or 'selling' in line.lower() or ':' in line:
                    current_option['features'] = line.split(':')[-1].strip()
        
        return hotel_options
    
    def answer_question(self, question, hotel_data):
        """Answer questions about hotel options."""
        prompt = f"""As a travel assistant, answer this question about hotel options:
        
        Hotel options:
        {hotel_data}
        
        Question: {question}
        
        Provide a helpful, detailed response about the hotels."""
        
        response = self.llm.invoke(prompt)
        return str(response)

    def modify_hotel_booking(self, travel_plan: TravelPlan) -> None:
        """Allow user to modify existing hotel booking"""
        if not travel_plan.hotels:
            print("No hotel booking to modify.")
            return
            
        print("\nCurrent hotel booking:")
        print(self.get_hotel_summary(travel_plan))
        
        print("\nWhat would you like to modify?")
        print("1. Cancel booking and search again")
        print("2. Adjust number of nights")
        print("3. Return to main menu")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            # Refund the previous booking cost
            travel_plan.remaining_budget += travel_plan.hotels.get('price', 0)
            travel_plan.hotels = None
            print(f"✅ Booking cancelled. Remaining budget: ${travel_plan.remaining_budget:.2f}")
            self.discuss_hotels(travel_plan)
        elif choice == '2':
            current_nights = travel_plan.hotels.get('nights', 0)
            current_price = travel_plan.hotels.get('price', 0)
            price_per_night = current_price / current_nights if current_nights > 0 else 0
            
            print(f"Current stay: {current_nights} nights at ${price_per_night:.2f}/night")
            new_nights = int(input("Enter new number of nights: "))
            
            if new_nights <= 0:
                print("Invalid number of nights.")
                return
                
            new_price = price_per_night * new_nights
            price_difference = new_price - current_price
            
            if price_difference > travel_plan.remaining_budget:
                print(f"⚠️ Insufficient funds. You need ${price_difference:.2f} more.")
                return
                
            # Update the booking
            travel_plan.remaining_budget -= price_difference
            travel_plan.hotels['nights'] = new_nights
            travel_plan.hotels['price'] = new_price
            
            print(f"✅ Booking updated to {new_nights} nights. New price: ${new_price:.2f}")
            print(f"Remaining budget: ${travel_plan.remaining_budget:.2f}")