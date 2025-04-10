"""
Activity service for managing activity-related operations
"""
from typing import Dict, Any, List
from datetime import datetime
from models.travel_plan import TravelPlan
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from utils.input_utils import get_numeric_input

class ActivityService:
    """Service for activity search and booking"""
    
    def __init__(self, llm: Any):
        self.llm = llm
        
    def discuss_activities(self, travel_plan: TravelPlan) -> None:
        """AI-generated activity suggestions based on remaining budget and destination"""
        if not travel_plan.hotels:
            print("\n🏨 Please book hotels first!")
            return
            
        # Calculate remaining days
        nights = travel_plan.get_trip_duration_days()
        daily_budget = travel_plan.remaining_budget / nights if nights > 0 else travel_plan.remaining_budget
        
        # AI Prompt Template
        prompt = PromptTemplate(
            input_variables=["destination", "budget"],
            template="""As a travel assistant, suggest 3-5 activities in {destination}
            with a total budget of ${budget:.2f}. For each activity include:
            - Activity name
            - Approximate cost per person
            - Time required (half-day/full-day)
            - Why it's worth doing
            - Category (cultural, adventure, relaxation, etc.)

            Format as a numbered list with clear sections."""
        )
        
        # Generate suggestions
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.invoke({
            "destination": travel_plan.destination['name'],
            "budget": travel_plan.remaining_budget
        })["text"]
        
        # Display results
        print(f"\n{'='*60}\n🎡 ACTIVITY SUGGESTIONS IN {travel_plan.destination['name'].upper()}\n{'='*60}")
        print(f"💰 Remaining Budget: ${travel_plan.remaining_budget:.2f} | 📅 {nights} days\n")
        print(response)
        
        # Use a direct prompt template approach instead of chains with memory
        inquiry_template = """You're a helpful activity planning assistant for {destination}.
        The user has a budget of ${budget:.2f}.
        
        Available activity options:
        {activities_info}
        
        The user's question is: {question}
        
        Please provide a detailed and helpful response about the activity options specifically addressing the user's question."""
        
        # Track booked activities
        if not hasattr(travel_plan, 'activities') or not travel_plan.activities:
            travel_plan.activities = []
        
        # Booking interaction
        while True:
            choice = input("\nChoose an option (1-5), [B] to see booked activities, [X] to finish, or ask a question about the options: ").strip().upper()
            
            if choice == 'X':
                if not travel_plan.activities:
                    print("No activities booked. Are you sure you want to skip? [Y/N]")
                    confirm = input().strip().upper()
                    if confirm != 'Y':
                        continue
                return
                
            if choice == 'B':
                self.show_booked_activities(travel_plan)
                continue
                
            if choice.isdigit() and 1 <= int(choice) <= 5:
                option_num = int(choice)
                
                # Use predefined activity information based on the option number
                activity_details = {
                    1: {"name": "City Tour", "category": "Cultural", "duration": "Half-day", 
                        "price": min(travel_plan.remaining_budget * 0.15, 50)},
                    2: {"name": "Museum Visit", "category": "Cultural", "duration": "Half-day", 
                        "price": min(travel_plan.remaining_budget * 0.10, 30)},
                    3: {"name": "Outdoor Adventure", "category": "Adventure", "duration": "Full-day", 
                        "price": min(travel_plan.remaining_budget * 0.25, 80)},
                    4: {"name": "Local Cuisine Experience", "category": "Culinary", "duration": "Half-day", 
                        "price": min(travel_plan.remaining_budget * 0.15, 60)},
                    5: {"name": "Evening Entertainment", "category": "Entertainment", "duration": "Evening", 
                        "price": min(travel_plan.remaining_budget * 0.15, 45)}
                }
                
                # Get details for selected option
                selected_activity = activity_details[option_num]
                
                # Show price and confirm
                price = selected_activity["price"]
                print(f"\nActivity Option {choice} - {selected_activity['name']}")
                print(f"Category: {selected_activity['category']} | Duration: {selected_activity['duration']}")
                print(f"Estimated price: ${price:.2f}")
                
                confirm = input("Confirm booking? (y/n): ").lower()
                
                if confirm == 'y':
                    if price <= travel_plan.remaining_budget:
                        # Add to booked activities
                        travel_plan.activities.append({
                            'option': option_num,
                            'name': selected_activity['name'],
                            'category': selected_activity['category'],
                            'duration': selected_activity['duration'],
                            'price': price
                        })
                        
                        # Update budget
                        travel_plan.remaining_budget -= price
                        print(f"✅ Activity booked! Remaining budget: ${travel_plan.remaining_budget:.2f}")
                        
                        # Ask if user wants to book another activity
                        if travel_plan.remaining_budget > 0:
                            book_another = input("Would you like to book another activity? [Y/N]: ").strip().upper()
                            if book_another != 'Y':
                                return
                        else:
                            print("Your budget is fully allocated. Finishing activity booking.")
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
                    activities_info=response,
                    question=choice
                )
                # Call the LLM directly with correct output handling
                response = str(self.llm.invoke(filled_prompt))
                print(f"\nAssistant: {response}")
    
    def show_booked_activities(self, travel_plan: TravelPlan) -> None:
        """Display all booked activities"""
        if not travel_plan.activities or len(travel_plan.activities) == 0:
            print("No activities booked yet.")
            return
            
        print(f"\n{'='*60}\n🎯 BOOKED ACTIVITIES\n{'='*60}")
        total_cost = 0
        for i, activity in enumerate(travel_plan.activities, 1):
            print(f"{i}. {activity['name']} - {activity['category']}")
            print(f"   Duration: {activity['duration']} | Cost: ${activity['price']:.2f}")
            total_cost += activity['price']
        print(f"\nTotal activities cost: ${total_cost:.2f}")
        print(f"Remaining budget: ${travel_plan.remaining_budget:.2f}")
        
    def get_activities_summary(self, travel_plan: TravelPlan) -> str:
        """Return a summary of booked activities"""
        if not travel_plan.activities or len(travel_plan.activities) == 0:
            return "No activities booked yet."
            
        summary = f"🎯 ACTIVITIES SUMMARY ({len(travel_plan.activities)} activities booked)\n"
        total_cost = 0
        
        for activity in travel_plan.activities:
            summary += f"- {activity['name']} ({activity['duration']}): ${activity['price']:.2f}\n"
            total_cost += activity['price']
            
        summary += f"\nTotal activities cost: ${total_cost:.2f}"
        return summary
        
    def get_activity_suggestions(self, destination, budget, days):
        """Get activity suggestions and return data instead of printing."""
        daily_budget = budget / days if days > 0 else budget
        
        # Generate suggestions using the LLM
        prompt = f"""As a travel assistant, suggest 5 activities in {destination}
        with a total budget of ${budget:.2f}. For each activity include:
        - Activity name
        - Approximate cost per person
        - Time required (half-day/full-day)
        - Why it's worth doing
        - Category (cultural, adventure, relaxation, etc.)
        
        Format as a structured list with clear sections."""
        
        response = self.llm.invoke(prompt)
        
        # Parse the response into a structured format
        activity_options = []
        current_option = {}
        
        for line in str(response).split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('1.') or line.startswith('Activity 1:'):
                current_option = {'option': 1}
                activity_options.append(current_option)
            elif line.startswith('2.') or line.startswith('Activity 2:'):
                current_option = {'option': 2}
                activity_options.append(current_option)
            elif line.startswith('3.') or line.startswith('Activity 3:'):
                current_option = {'option': 3}
                activity_options.append(current_option)
            elif line.startswith('4.') or line.startswith('Activity 4:'):
                current_option = {'option': 4}
                activity_options.append(current_option)
            elif line.startswith('5.') or line.startswith('Activity 5:'):
                current_option = {'option': 5}
                activity_options.append(current_option)
            
            # Parse activity details
            if 'option' in current_option:
                if 'name' not in current_option and ':' not in line and len(line) > 5:
                    current_option['name'] = line
                elif 'cost' in line.lower() or 'price' in line.lower() or '$' in line:
                    try:
                        price_text = line.split('$')[1].split()[0].replace(',', '')
                        current_option['price'] = float(price_text)
                    except:
                        # Estimate a price if parsing fails
                        current_option['price'] = daily_budget * (0.1 * current_option['option'])
                elif 'duration' in line.lower() or 'time' in line.lower() or 'hour' in line.lower():
                    current_option['duration'] = line.split(':')[-1].strip()
                elif 'worth' in line.lower() or 'why' in line.lower():
                    current_option['value'] = line.split(':')[-1].strip()
                elif 'category' in line.lower() or 'type' in line.lower():
                    current_option['category'] = line.split(':')[-1].strip()
        
        return activity_options
    
    def answer_question(self, question, activity_data):
        """Answer questions about activity options."""
        prompt = f"""As a travel assistant, answer this question about activity options:
        
        Activity options:
        {activity_data}
        
        Question: {question}
        
        Provide a helpful, detailed response about the activities."""
        
        response = self.llm.invoke(prompt)
        return str(response)

    def modify_activities(self, travel_plan: TravelPlan) -> None:
        """Allow user to modify booked activities"""
        if not travel_plan.activities or len(travel_plan.activities) == 0:
            print("No activities to modify.")
            return
            
        while True:
            print("\nCurrent activities:")
            self.show_booked_activities(travel_plan)
            
            print("\nWhat would you like to do?")
            print("1. Remove an activity")
            print("2. Add new activities")
            print("3. Return to main menu")
            
            choice = input("Enter your choice (1-3): ")
            
            if choice == '1':
                # Remove activity
                if len(travel_plan.activities) == 0:
                    print("No activities to remove.")
                    continue
                    
                index = get_numeric_input("Enter the number of the activity to remove: ")
                
                if not index.is_integer() or index < 1 or index > len(travel_plan.activities):
                    print("Invalid activity number.")
                    continue
                    
                index = int(index)
                removed = travel_plan.activities.pop(index - 1)
                travel_plan.remaining_budget += removed['price']
                print(f"✅ Removed: {removed['name']}. Refunded: ${removed['price']:.2f}")
                print(f"New remaining budget: ${travel_plan.remaining_budget:.2f}")
                
            elif choice == '2':
                # Add new activities
                self.discuss_activities(travel_plan)
                return
                
            elif choice == '3':
                return
                
            else:
                print("Invalid choice. Please enter a number between 1 and 3.")