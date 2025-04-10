"""
Utility functions for date validation, manipulation and formatting
used throughout the travel planner application.
"""

from datetime import datetime, timedelta
import calendar
import re

def validate_date_format(date_str):
    """
    Validates if the provided string is in the correct date format (YYYY-MM-DD).
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def is_future_date(date_str):
    """
    Checks if the provided date is in the future.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        bool: True if date is in the future, False otherwise
    """
    if not validate_date_format(date_str):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    today = datetime.now().date()
    
    return date_obj > today

def calculate_trip_duration(start_date, end_date):
    """
    Calculate the duration of a trip in days.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        int: Number of days for the trip
    """
    if not (validate_date_format(start_date) and validate_date_format(end_date)):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if end < start:
        raise ValueError("End date cannot be before start date")
    
    duration = (end - start).days + 1  # Include both start and end days
    return duration

def is_valid_date_range(start_date, end_date, max_days=30):
    """
    Validates if the date range is valid and within allowed limits.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        max_days (int): Maximum allowed duration in days
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not (validate_date_format(start_date) and validate_date_format(end_date)):
            return False
        
        if not is_future_date(start_date):
            return False
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if end < start:
            return False
        
        duration = (end - start).days + 1
        if duration > max_days:
            return False
            
        return True
    except ValueError:
        return False

def format_date_display(date_str, format_str='%B %d, %Y'):
    """
    Formats date string for display purposes.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        format_str (str): Output format string
        
    Returns:
        str: Formatted date string
    """
    if not validate_date_format(date_str):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.strftime(format_str)

def get_day_of_week(date_str):
    """
    Returns the day of week for a given date.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        str: Day of week (e.g., "Monday")
    """
    if not validate_date_format(date_str):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.strftime('%A')

def add_days(date_str, days):
    """
    Add specified number of days to a date.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        days (int): Number of days to add
        
    Returns:
        str: Resulting date in YYYY-MM-DD format
    """
    if not validate_date_format(date_str):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    new_date = date_obj + timedelta(days=days)
    return new_date.strftime('%Y-%m-%d')

def get_date_range_list(start_date, end_date):
    """
    Generate a list of dates between start and end dates (inclusive).
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        list: List of date strings in YYYY-MM-DD format
    """
    if not (validate_date_format(start_date) and validate_date_format(end_date)):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if end < start:
        raise ValueError("End date cannot be before start date")
    
    date_list = []
    current = start
    
    while current <= end:
        date_list.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return date_list

def is_high_season(date_str, location=None):
    """
    Determine if a date is likely to be in high season.
    This is a simple implementation based on common travel patterns.
    For more accurate results, location-specific logic should be added.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        location (str, optional): Location name to check against
        
    Returns:
        bool: True if likely high season, False otherwise
    """
    if not validate_date_format(date_str):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    month = date_obj.month
    
    # Simple default high season logic (northern hemisphere summer, winter holidays)
    if month in [6, 7, 8, 12]:
        return True
    
    # If location specific logic is added, it would go here
    # For example, beach destinations vs ski resorts
    
    return False