"""Configuration settings for Arizona House Hunter."""

# Search Parameters
SEARCH_CITIES = {
    "phoenix_metro": ["Gilbert, AZ", "Chandler, AZ", "Scottsdale, AZ", "Mesa, AZ"],
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
    "Scottsdale": 1.00,
    "Gilbert": 0.97,
    "Chandler": 0.94,
    "Queen Creek": 0.92,
    "Oro Valley": 0.91,
    "Green Valley": 0.89,
    "Mesa": 0.86,
    "Marana": 0.84,
    "Tucson": 0.83,
    "Vail": 0.82,
    "Apache Junction": 0.80,
}

# Scraping settings
REQUEST_DELAY_SECONDS = 2.5  # Delay between requests to avoid blocks
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Database settings
DATABASE_PATH = "house_hunter/data/listings.db"

# Flask settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True
