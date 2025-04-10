#!/usr/bin/env python
"""
Travel Planner - Main entry point
"""
import sys
from config import load_api_keys
from models.travel_plan import TravelPlan
from ui.cli import TravelPlannerCLI
from services.flight_service import FlightService
from services.hotel_service import HotelService
from services.activity_service import ActivityService
from langchain_openai import OpenAI



def main():
    """Main application entry point"""
    print("Welcome to Travel Planner!")
    print("Loading configuration...")
    
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
    
    # Create new travel plan
    travel_plan = TravelPlan()
    
    # Initialize UI with services
    cli = TravelPlannerCLI(
        travel_plan=travel_plan,
        flight_service=flight_service,
        hotel_service=hotel_service,
        activity_service=activity_service
    )
    
    # Run the CLI
    cli.collect_initial_details()
    cli.show_main_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTravel planning interrupted. Goodbye!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please try again later.")