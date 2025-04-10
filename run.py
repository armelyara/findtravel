#!/usr/bin/env python
"""
Run script for Travel Planner
"""
import sys
from main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTravel planning interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please try again later.")
        sys.exit(1)