"""
Travel plan model
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import json


class TravelPlan:
    """Travel plan class with validation and helper methods"""
    def __init__(self):
        self.total_budget: Optional[float] = None
        self.remaining_budget: Optional[float] = None
        self.departure: Dict[str, Optional[str]] = {'name': None, 'iata': None}
        self.destination: Dict[str, Optional[str]] = {'name': None, 'iata': None}
        self.departure_date: Optional[str] = None
        self.return_date: Optional[str] = None
        self.travelers: Optional[int] = None
        self.flights: Optional[Dict[str, Any]] = None
        self.hotels: Optional[Dict[str, Any]] = None
        self.activities: List[Dict[str, Any]] = []  # List to allow multiple activities
        
    def calculate_remaining_budget(self) -> float:
        """Calculate remaining budget based on all bookings"""
        spent = 0
        if self.flights and 'price' in self.flights:
            spent += self.flights['price']
        if self.hotels and 'price' in self.hotels:
            spent += self.hotels['price']
        for activity in self.activities:
            if 'price' in activity:
                spent += activity['price']
        
        self.remaining_budget = self.total_budget - spent
        return self.remaining_budget
    
    def get_trip_duration_days(self) -> int:
        """Calculate trip duration in days"""
        if not self.departure_date or not self.return_date:
            return 0
        try:
            delta = datetime.strptime(self.return_date, "%Y-%m-%d") - datetime.strptime(self.departure_date, "%Y-%m-%d")
            return delta.days
        except ValueError:
            return 0
            
    def to_dict(self) -> Dict:
        """Convert travel plan to dictionary for serialization"""
        return {
            'total_budget': self.total_budget,
            'remaining_budget': self.remaining_budget,
            'departure': self.departure,
            'destination': self.destination,
            'departure_date': self.departure_date,
            'return_date': self.return_date,
            'travelers': self.travelers,
            'flights': self.flights,
            'hotels': self.hotels,
            'activities': self.activities
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'TravelPlan':
        """Create travel plan from dictionary"""
        plan = cls()
        for key, value in data.items():
            setattr(plan, key, value)
        return plan
    
    def save_to_file(self, filename: str) -> None:
        """Save travel plan to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load_from_file(cls, filename: str) -> Optional['TravelPlan']:
        """Load travel plan from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                return cls.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
            
    def get_summary(self) -> str:
        """Generate a summary of the travel plan"""
        summary = f"TRAVEL PLAN SUMMARY\n{'='*50}\n"
        summary += f"Trip: {self.departure['name']} → {self.destination['name']}\n"
        summary += f"Dates: {self.departure_date} to {self.return_date} ({self.get_trip_duration_days()} days)\n"
        summary += f"Travelers: {self.travelers}\n"
        summary += f"Budget: ${self.total_budget:.2f} (${self.remaining_budget:.2f} remaining)\n\n"
        
        if self.flights:
            summary += f"FLIGHT: Option {self.flights['option']} - ${self.flights['price']:.2f}\n"
            
        if self.hotels:
            summary += f"HOTEL: Option {self.hotels['option']} - ${self.hotels['price']:.2f}\n"
            
        if self.activities:
            summary += "ACTIVITIES:\n"
            for activity in self.activities:
                summary += f"- Option {activity['option']} - ${activity['price']:.2f}\n"
                
        return summary