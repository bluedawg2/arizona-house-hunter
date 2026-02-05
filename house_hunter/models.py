"""Data models for house listings."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Listing:
    """Represents a real estate listing with all relevant data."""

    # Core identification
    id: str  # Unique identifier (e.g., Redfin listing ID)
    source: str  # "redfin", "zillow", etc.
    url: str  # Direct link to listing

    # Location
    address: str
    city: str
    state: str = "AZ"
    zip_code: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Price
    price: int = 0

    # Property details
    beds: int = 0
    baths: float = 0.0
    sqft: int = 0
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: str = ""  # "single_family", "townhouse", etc.
    stories: Optional[int] = None  # Number of stories (1=ranch, 2=two-story, etc.)

    # Costs
    hoa_monthly: Optional[int] = None
    annual_tax: Optional[int] = None

    # Market data
    days_on_market: Optional[int] = None
    list_date: Optional[str] = None

    # Features (boolean flags)
    has_pool: bool = False
    has_yard: bool = False
    has_solar: bool = False
    has_garage: bool = False
    has_basement: bool = False
    garage_spaces: int = 0

    # Enrichment data
    walk_score: Optional[int] = None
    crime_index: Optional[int] = None
    distance_to_downtown: Optional[float] = None
    nearest_downtown: Optional[str] = None

    # Calculated score
    value_score: Optional[float] = None

    # Metadata
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    photo_url: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert listing to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "url": self.url,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "price": self.price,
            "beds": self.beds,
            "baths": self.baths,
            "sqft": self.sqft,
            "lot_sqft": self.lot_sqft,
            "year_built": self.year_built,
            "property_type": self.property_type,
            "stories": self.stories,
            "hoa_monthly": self.hoa_monthly,
            "annual_tax": self.annual_tax,
            "days_on_market": self.days_on_market,
            "list_date": self.list_date,
            "has_pool": self.has_pool,
            "has_yard": self.has_yard,
            "has_solar": self.has_solar,
            "has_garage": self.has_garage,
            "has_basement": self.has_basement,
            "garage_spaces": self.garage_spaces,
            "walk_score": self.walk_score,
            "crime_index": self.crime_index,
            "distance_to_downtown": self.distance_to_downtown,
            "nearest_downtown": self.nearest_downtown,
            "value_score": self.value_score,
            "last_updated": self.last_updated,
            "photo_url": self.photo_url,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Listing":
        """Create a Listing from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def passes_hard_filters(self) -> bool:
        """Check if listing passes all hard filter requirements."""
        from . import config

        # Beds check
        if self.beds < config.MIN_BEDS:
            return False

        # Baths check
        if self.baths < config.MIN_BATHS:
            return False

        # Square footage check
        if self.sqft < config.MIN_SQFT:
            return False

        # Price check
        if self.price > config.PRICE_RANGE[1]:
            return False

        # Year built check
        if self.year_built and self.year_built < config.MIN_YEAR_BUILT:
            return False

        # Property type check (no condos, apartments, or manufactured/other)
        if self.property_type.lower() in ["condo", "condominium", "apartment", "other", "manufactured"]:
            return False

        # Fractional/co-ownership check
        if self.description:
            desc_lower = self.description.lower()
            fractional_keywords = [
                "co-ownership", "coownership", "co ownership",
                "fractional", "timeshare", "time share",
                "1/8 ownership", "1/4 ownership", "1/2 ownership",
                "shared ownership", "partial ownership",
                ".125 ownership", ".25 ownership", ".5 ownership",
            ]
            for keyword in fractional_keywords:
                if keyword in desc_lower:
                    return False

        return True
