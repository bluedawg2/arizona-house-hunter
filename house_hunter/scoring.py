"""Value scoring engine for ranking listings."""

import logging
from typing import List, Optional
from statistics import mean, stdev

from .models import Listing
from . import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_value(value: float, values: List[float], invert: bool = False) -> float:
    """
    Normalize a value to 0-1 range based on min/max of all values.
    If invert=True, lower values get higher scores.
    """
    if not values or len(values) < 2:
        return 0.5

    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return 0.5

    normalized = (value - min_val) / (max_val - min_val)

    if invert:
        normalized = 1 - normalized

    return max(0, min(1, normalized))  # Clamp to 0-1


def calculate_value_score(listing: Listing, all_listings: List[Listing]) -> float:
    """
    Calculate a value score from 0-100 for a listing.
    Higher scores indicate better value.

    Weights (from config):
    - sqft_value: 23 - Square footage per dollar
    - year_built: 20 - Newer is better
    - location: 20 - Preferred cities
    - low_hoa: 10 - Lower HOA is better
    - low_taxes: 9 - Lower taxes is better
    - private_yard: 9 - Private fenced yard (dog friendly)
    - days_on_market: 3 - Higher DOM = potential deal
    - pool: 3 - Has pool
    - solar: 3 - Has solar
    """
    scores = {}
    weights = config.WEIGHTS

    # Collect values from all listings for normalization
    sqft_per_dollar_values = []
    year_values = []
    hoa_values = []
    dom_values = []

    for l in all_listings:
        if l.price > 0 and l.sqft > 0:
            sqft_per_dollar_values.append(l.sqft / l.price)
        if l.year_built:
            year_values.append(l.year_built)
        if l.hoa_monthly is not None:
            hoa_values.append(l.hoa_monthly)
        if l.days_on_market is not None:
            dom_values.append(l.days_on_market)

    # 1. Square footage per dollar (higher = better value)
    if listing.price > 0 and listing.sqft > 0:
        sqft_per_dollar = listing.sqft / listing.price
        scores["sqft_value"] = normalize_value(
            sqft_per_dollar, sqft_per_dollar_values
        ) * weights["sqft_value"]
    else:
        scores["sqft_value"] = 0

    # 2. Year built (newer = better)
    if listing.year_built and year_values:
        scores["year_built"] = normalize_value(
            listing.year_built, year_values
        ) * weights["year_built"]
    else:
        scores["year_built"] = weights["year_built"] * 0.5  # Default to middle

    # 3. Low HOA (lower = better, so invert)
    if listing.hoa_monthly is not None and hoa_values:
        scores["low_hoa"] = normalize_value(
            listing.hoa_monthly, hoa_values, invert=True
        ) * weights["low_hoa"]
    else:
        # No HOA is best
        scores["low_hoa"] = weights["low_hoa"]

    # 4. Location preference
    location_weight = config.LOCATION_WEIGHTS.get(listing.city, 0.80)  # Default for unknown cities
    scores["location"] = location_weight * weights["location"]

    # 5. Private yard (boolean - important for dog)
    scores["private_yard"] = weights["private_yard"] if listing.has_yard else 0

    # 6. Days on market (higher = potential deal)
    if listing.days_on_market is not None and dom_values:
        scores["days_on_market"] = normalize_value(
            listing.days_on_market, dom_values
        ) * weights["days_on_market"]
    else:
        scores["days_on_market"] = weights["days_on_market"] * 0.5

    # 7. Pool (boolean)
    scores["pool"] = weights["pool"] if listing.has_pool else 0

    # 8. Solar (boolean)
    scores["solar"] = weights["solar"] if listing.has_solar else 0

    total_score = sum(scores.values())

    # Log breakdown for debugging
    logger.debug(f"Listing {listing.id} score breakdown: {scores} = {total_score}")

    return round(total_score, 1)


def score_all_listings(listings: List[Listing]) -> List[Listing]:
    """
    Calculate value scores for all listings.
    Modifies listings in place and returns them sorted by score (descending).
    """
    logger.info(f"Scoring {len(listings)} listings...")

    # Filter to only valid listings for scoring
    valid_listings = [l for l in listings if l.price > 0]

    for listing in valid_listings:
        listing.value_score = calculate_value_score(listing, valid_listings)

    # Sort by value score (highest first)
    valid_listings.sort(key=lambda l: l.value_score or 0, reverse=True)

    logger.info(f"Scoring complete. Top score: {valid_listings[0].value_score if valid_listings else 'N/A'}")

    return valid_listings


def get_score_breakdown(listing: Listing, all_listings: List[Listing]) -> dict:
    """
    Get a detailed breakdown of how a listing's score was calculated.
    Useful for displaying to users.
    """
    weights = config.WEIGHTS
    breakdown = {}

    # Collect values from all listings for normalization
    sqft_per_dollar_values = [l.sqft / l.price for l in all_listings if l.price > 0 and l.sqft > 0]
    year_values = [l.year_built for l in all_listings if l.year_built]
    hoa_values = [l.hoa_monthly for l in all_listings if l.hoa_monthly is not None]
    dom_values = [l.days_on_market for l in all_listings if l.days_on_market is not None]

    # Sqft per dollar
    if listing.price > 0 and listing.sqft > 0:
        sqft_per_dollar = listing.sqft / listing.price
        raw_score = normalize_value(sqft_per_dollar, sqft_per_dollar_values)
        breakdown["sqft_value"] = {
            "weight": weights["sqft_value"],
            "raw_value": round(sqft_per_dollar * 1000, 2),  # sqft per $1000
            "normalized": round(raw_score, 2),
            "points": round(raw_score * weights["sqft_value"], 1),
            "description": f"{round(sqft_per_dollar * 1000, 1)} sqft per $1000"
        }

    # Year built
    if listing.year_built:
        raw_score = normalize_value(listing.year_built, year_values)
        breakdown["year_built"] = {
            "weight": weights["year_built"],
            "raw_value": listing.year_built,
            "normalized": round(raw_score, 2),
            "points": round(raw_score * weights["year_built"], 1),
            "description": f"Built in {listing.year_built}"
        }

    # HOA
    hoa_val = listing.hoa_monthly if listing.hoa_monthly is not None else 0
    if hoa_values:
        raw_score = normalize_value(hoa_val, hoa_values, invert=True)
    else:
        raw_score = 1 if hoa_val == 0 else 0.5
    breakdown["low_hoa"] = {
        "weight": weights["low_hoa"],
        "raw_value": hoa_val,
        "normalized": round(raw_score, 2),
        "points": round(raw_score * weights["low_hoa"], 1),
        "description": f"${hoa_val}/month HOA" if hoa_val else "No HOA"
    }

    # Location
    location_weight = config.LOCATION_WEIGHTS.get(listing.city, 0.80)
    breakdown["location"] = {
        "weight": weights["location"],
        "raw_value": listing.city,
        "normalized": round(location_weight, 2),
        "points": round(location_weight * weights["location"], 1),
        "description": f"{listing.city} ({location_weight:.0%} preference)"
    }

    # Yard
    breakdown["private_yard"] = {
        "weight": weights["private_yard"],
        "raw_value": listing.has_yard,
        "normalized": 1 if listing.has_yard else 0,
        "points": weights["private_yard"] if listing.has_yard else 0,
        "description": "Has yard" if listing.has_yard else "No yard"
    }

    # DOM
    if listing.days_on_market is not None and dom_values:
        raw_score = normalize_value(listing.days_on_market, dom_values)
        breakdown["days_on_market"] = {
            "weight": weights["days_on_market"],
            "raw_value": listing.days_on_market,
            "normalized": round(raw_score, 2),
            "points": round(raw_score * weights["days_on_market"], 1),
            "description": f"{listing.days_on_market} days on market"
        }

    # Pool
    breakdown["pool"] = {
        "weight": weights["pool"],
        "raw_value": listing.has_pool,
        "normalized": 1 if listing.has_pool else 0,
        "points": weights["pool"] if listing.has_pool else 0,
        "description": "Has pool" if listing.has_pool else "No pool"
    }

    # Solar
    breakdown["solar"] = {
        "weight": weights["solar"],
        "raw_value": listing.has_solar,
        "normalized": 1 if listing.has_solar else 0,
        "points": weights["solar"] if listing.has_solar else 0,
        "description": "Has solar" if listing.has_solar else "No solar"
    }

    return breakdown
