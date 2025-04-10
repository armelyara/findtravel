"""
Utility functions for handling user input with validation
"""
from datetime import datetime
from typing import Union, Optional
from utils.date_utils import validate_date_format

def get_numeric_input(prompt: str, min_value: float = 0, 
                     max_value: float = float('inf'), 
                     allow_float: bool = True) -> float:
    """
    Get numeric input from user with validation.
    
    Args:
        prompt: The prompt to display
        min_value: Minimum acceptable value
        max_value: Maximum acceptable value
        allow_float: Whether to allow floating point numbers
        
    Returns:
        Numeric value from user
    """
    while True:
        try:
            value = input(prompt).strip()
            if not value:
                print("This field is required. Please try again.")
                continue
            
            num = float(value)
            if not allow_float and num != int(num):
                print("Please enter a whole number.")
                continue
                
            if num < min_value or num > max_value:
                print(f"Please enter a value between {min_value} and {max_value}.")
                continue
                
            return int(num) if not allow_float else num
        except ValueError:
            print("Please enter a valid number.")

def get_date_input(prompt: str, min_date: Optional[str] = None,
                  reference_date: Optional[str] = None) -> str:
    """
    Get date input from user with validation.
    
    Args:
        prompt: The prompt to display
        min_date: Minimum acceptable date (YYYY-MM-DD format)
        reference_date: Reference date for validation (YYYY-MM-DD format)
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    while True:
        date_str = input(prompt).strip()
        
        if not validate_date_format(date_str):
            print("Invalid date format. Please use YYYY-MM-DD.")
            continue
            
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        if min_date:
            min_date_obj = datetime.strptime(min_date, "%Y-%m-%d")
            if date_obj < min_date_obj:
                print(f"Date must be on or after {min_date}.")
                continue
        
        if reference_date:
            ref_date_obj = datetime.strptime(reference_date, "%Y-%m-%d")
            if date_obj < ref_date_obj:
                print(f"Date must be on or after {reference_date}.")
                continue
                
        return date_str

def get_yes_no_input(prompt: str) -> bool:
    """
    Get a yes/no answer from the user.
    
    Args:
        prompt: The prompt to display
        
    Returns:
        Boolean representing user's choice (True for yes, False for no)
    """
    while True:
        response = input(prompt).strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please enter 'y' or 'n'.")

def get_choice_input(prompt: str, options: list, allow_other: bool = False) -> str:
    """
    Get user choice from a list of options.
    
    Args:
        prompt: The prompt to display
        options: List of valid options
        allow_other: Whether to allow input not in options
        
    Returns:
        User's selected option
    """
    options_display = ", ".join(options)
    while True:
        choice = input(f"{prompt} [{options_display}]: ").strip()
        
        if choice in options:
            return choice
        elif allow_other:
            confirm = input(f"'{choice}' is not in the suggested options. Use anyway? (y/n): ").lower()
            if confirm == 'y':
                return choice
        else:
            print(f"Please select one of: {options_display}")