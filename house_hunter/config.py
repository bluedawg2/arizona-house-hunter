"""Configuration settings for Arizona House Hunter."""

# Search Parameters
SEARCH_CITIES = {
    "phoenix_metro": ["Gilbert, AZ", "Chandler, AZ", "Scottsdale, AZ", "Mesa, AZ", "Surprise, AZ"],
    "tucson_area": ["Tucson, AZ", "Green Valley, AZ", "Oro Valley, AZ"]
}

# Redfin city/region IDs for API calls (correct Arizona region IDs)
REDFIN_REGIONS = {
    "Gilbert": {"type": "city", "id": 6998, "state": "AZ"},
    "Chandler": {"type": "city", "id": 3104, "state": "AZ"},
    "Scottsdale": {"type": "city", "id": 16660, "state": "AZ"},
    "Mesa": {"type": "city", "id": 11736, "state": "AZ"},
    "Tucson": {"type": "city", "id": 19459, "state": "AZ"},
    "Green Valley": {"type": "city", "id": 23055, "state": "AZ"},
    "Oro Valley": {"type": "city", "id": 13300, "state": "AZ"},
    "Surprise": {"type": "city", "id": 18267, "state": "AZ"},
}

# Price and property filters
PRICE_RANGE = (400000, 700000)
IDEAL_PRICE_RANGE = (400000, 600000)
MIN_BEDS = 3
MIN_BATHS = 2
MIN_SQFT = 1200
MAX_AGE_YEARS = 30
MIN_YEAR_BUILT = 1996
PROPERTY_TYPES = ["single_family", "townhouse"]

# Downtown coordinates for distance calculations
DOWNTOWN_COORDS = {
    "Phoenix": (33.4484, -112.0740),
    "Scottsdale": (33.4942, -111.9261),
    "Gilbert": (33.3528, -111.7890),
    "Chandler": (33.3062, -111.8413),
    "Mesa": (33.4152, -111.8315),
    "Tucson": (32.2226, -110.9747),
    "Green Valley": (31.8543, -110.9932),
    "Oro Valley": (32.3909, -110.9665),
    "Surprise": (33.6306, -112.3332),
}

# City-level crime indices (higher = safer, scale 0-100)
# Based on published crime statistics - relative safety scores
CITY_CRIME_INDEX = {
    "Gilbert": 85,          # Very safe
    "Chandler": 78,         # Safe
    "Scottsdale": 75,       # Safe
    "Queen Creek": 82,      # Very safe (newer community)
    "Mesa": 55,             # Moderate
    "Tucson": 45,           # Below average
    "Green Valley": 80,     # Safe (retirement community)
    "Oro Valley": 78,       # Safe (Tucson suburb)
    "Marana": 70,           # Safe (Tucson suburb)
    "Vail": 75,             # Safe (Tucson suburb)
    "Surprise": 80,         # Safe (growing retiree community)
    "Apache Junction": 50,  # Moderate
}

# Scoring weights (must sum to 100)
WEIGHTS = {
    "location": 25,        # Preferred cities
    "sqft_value": 23,      # Sq ft per dollar
    "year_built": 20,      # Newer is better
    "low_hoa": 13,         # Lower HOA is better
    "private_yard": 10,    # Private fenced yard (dog friendly)
    "days_on_market": 3,   # Potential deal indicator
    "pool": 3,             # Nice to have
    "solar": 3,            # Nice to have
}

# Location preference weights (0-1 scale, higher = more preferred)
LOCATION_WEIGHTS = {
    "Scottsdale": 1.00,       # Family proximity + top retiree amenities
    "Gilbert": 0.97,          # #2 US News AZ retire, top safety/value
    "Surprise": 0.95,         # #1 US News AZ retire (83 US), elite safety/value
    "Chandler": 0.93,         # Top-5 AZ retire (187 US), healthcare balance
    "Green Valley": 0.90,     # 55+ golf haven, top Niche retiree
    "Oro Valley": 0.87,       # Strong Niche retiree, healthcare access
    "Queen Creek": 0.85,      # #3 US News AZ retire (154 US), value growth
    "Mesa": 0.82,             # Affordable healthcare hub
    "Marana": 0.80,           # #5 AZ retire (159 US), value
    "Apache Junction": 0.77,  # Budget retiree value
    "Vail": 0.75,             # Quiet safety
    "Tucson": 0.72,           # Amenities but urban crime
}

# Scraping settings
REQUEST_DELAY_SECONDS = 2.5  # Delay between requests to avoid blocks
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Database settings
# Use temp directory for Streamlit Cloud compatibility
import os
import tempfile

if os.environ.get("STREAMLIT_SERVER_HEADLESS"):
    # Running on Streamlit Cloud - use temp directory
    DATABASE_PATH = os.path.join(tempfile.gettempdir(), "listings.db")
else:
    # Local development
    DATABASE_PATH = "house_hunter/data/listings.db"

# Flask settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True
