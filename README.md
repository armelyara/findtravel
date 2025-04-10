# FindTravel: AI-powered Travel Planning Assistant

FindTravel is an intelligent travel planning assistant that helps users plan complete trips including flights, accommodations, and activities. It uses large language models to interact naturally with users and provide personalized recommendations.

## Features

- Interactive command-line interface for travel planning
- Search for flights between cities with real-time data
- Get hotel recommendations based on your destination and budget
- Discover activities and attractions at your destination
- Save and load travel plans
- Budget tracking and management

## Requirements

- Python 3.8+
- API Keys:
  - OpenAI API key
  - Google Maps API key (optional)
  - Amadeus API (optional)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/findtravel.git
   cd findtravel
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv trav_venv
   source trav_venv/bin/activate  # On Windows: trav_venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables for API keys:
   ```
   export OPENAI_API_KEY="your_openai_key"
   export GOOGLE_MAPS_API_KEY="your_google_maps_key"
   export AMADEUS_CLIENT_ID="your_amadeus_id"
   export AMADEUS_CLIENT_SECRET="your_amadeus_secret"
   ```

## Usage

Run the application:
```
python run.py
```

or make it executable:
```
chmod +x run.py
./run.py
```

## Project Structure

- `main.py`: Main entry point
- `config.py`: Configuration and API key management
- `models/`: Data models
- `services/`: Service classes for API interactions
- `ui/`: User interface code
- `utils/`: Utility functions

