"""Data enrichment module for adding walk scores, crime data, and distance calculations."""

import logging
from typing import List, Optional, Tuple
from math import radians, sin, cos, sqrt, atan2

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from .models import Listing
from . import config
from . import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeoEnricher:
    """Handles geocoding and distance calculations."""

    def __init__(self):
        self.geocoder = Nominatim(user_agent="arizona_house_hunter_v1")

    def geocode_address(self, address: str, city: str, state: str = "AZ") -> Optional[Tuple[float, float]]:
        """
        Geocode an address to latitude/longitude.
        Returns (latitude, longitude) or None if geocoding fails.
        """
        # Check cache first
        full_address = f"{address}, {city}, {state}"
        cached = database.get_enrichment_cache(full_address)
        if cached and cached.get("latitude") and cached.get("longitude"):
            return (cached["latitude"], cached["longitude"])

        try:
            location = self.geocoder.geocode(full_address, timeout=10)
            if location:
                lat, lon = location.latitude, location.longitude
                # Cache the result
                database.save_enrichment_cache(full_address, None, lat, lon)
                return (lat, lon)
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding failed for {full_address}: {e}")

        return None

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.
        Returns distance in miles.
        """
        R = 3959  # Earth's radius in miles

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def get_nearest_downtown(
        self, lat: float, lon: float
    ) -> Tuple[str, float]:
        """
        Find the nearest downtown and return its name and distance.
        Returns (downtown_name, distance_in_miles).
        """
        nearest = None
        min_distance = float("inf")

        for downtown, (d_lat, d_lon) in config.DOWNTOWN_COORDS.items():
            distance = self.calculate_distance(lat, lon, d_lat, d_lon)
            if distance < min_distance:
                min_distance = distance
                nearest = downtown

        return (nearest or "Unknown", round(min_distance, 1))


def get_crime_index(city: str) -> int:
    """
    Get the crime safety index for a city.
    Higher values = safer (scale 0-100).
    """
    # Normalize city name for lookup
    city_normalized = city.strip().title()

    # Handle variations
    if "Green Valley" in city_normalized:
        city_normalized = "Green Valley"

    return config.CITY_CRIME_INDEX.get(city_normalized, 50)  # Default to 50 if unknown


def enrich_listing(listing: Listing, geo_enricher: Optional[GeoEnricher] = None) -> Listing:
    """
    Enrich a single listing with additional data.
    Modifies the listing in place and returns it.
    """
    if geo_enricher is None:
        geo_enricher = GeoEnricher()

    # Add crime index based on city
    listing.crime_index = get_crime_index(listing.city)

    # Geocode if coordinates missing
    if not listing.latitude or not listing.longitude:
        coords = geo_enricher.geocode_address(listing.address, listing.city)
        if coords:
            listing.latitude, listing.longitude = coords

    # Calculate distance to nearest downtown
    if listing.latitude and listing.longitude:
        nearest, distance = geo_enricher.get_nearest_downtown(
            listing.latitude, listing.longitude
        )
        listing.nearest_downtown = nearest
        listing.distance_to_downtown = distance

    # Try to infer yard from lot size if not already set
    if not listing.has_yard and listing.lot_sqft:
        # Properties with lot > 3000 sqft likely have a yard
        listing.has_yard = listing.lot_sqft > 3000

    return listing


def enrich_all_listings(listings: List[Listing]) -> List[Listing]:
    """
    Enrich all listings with additional data.
    Returns the enriched listings.
    """
    logger.info(f"Enriching {len(listings)} listings...")
    geo_enricher = GeoEnricher()

    enriched = []
    for i, listing in enumerate(listings):
        try:
            enriched_listing = enrich_listing(listing, geo_enricher)
            enriched.append(enriched_listing)

            if (i + 1) % 10 == 0:
                logger.info(f"Enriched {i + 1}/{len(listings)} listings")

        except Exception as e:
            logger.warning(f"Failed to enrich listing {listing.id}: {e}")
            enriched.append(listing)  # Keep original if enrichment fails

    logger.info(f"Enrichment complete. {len(enriched)} listings processed.")
    return enriched
