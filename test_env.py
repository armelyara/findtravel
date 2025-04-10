import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print the environment variables
print("OPENAI_API_KEY:", os.environ.get("OPENAI_API_KEY", "Not found"))
print("GOOGLE_MAPS_API_KEY:", os.environ.get("GOOGLE_MAPS_API_KEY", "Not found"))
print("AMADEUS_CLIENT_ID:", os.environ.get("AMADEUS_CLIENT_ID", "Not found"))
print("AMADEUS_CLIENT_SECRET:", os.environ.get("AMADEUS_CLIENT_SECRET", "Not found"))