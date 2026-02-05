"""API route handlers for the Flask application."""

import logging
from typing import List, Optional
from flask import Blueprint, jsonify, request

from . import database
from . import config
from .models import Listing
from .fetcher import fetch_listings
from .enrichment import enrich_all_listings
from .scoring import score_all_listings, get_score_breakdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/listings", methods=["GET"])
def get_listings():
    """
    Get filtered and scored listings.

    Query Parameters:
    - min_price: Minimum price
    - max_price: Maximum price
    - min_beds: Minimum bedrooms
    - min_baths: Minimum bathrooms
    - min_sqft: Minimum square footage
    - cities: Comma-separated list of cities
    - has_yard: Filter for yard (true/false)
    - has_pool: Filter for pool (true/false)
    - has_solar: Filter for solar (true/false)
    - max_age: Maximum age in years
    - sort_by: Field to sort by (default: value_score)
    - sort_dir: Sort direction (asc/desc, default: desc)
    """
    # Parse query parameters
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_beds = request.args.get("min_beds", type=int)
    min_baths = request.args.get("min_baths", type=float)
    min_sqft = request.args.get("min_sqft", type=int)
    cities_param = request.args.get("cities", "")
    cities = [c.strip() for c in cities_param.split(",") if c.strip()] if cities_param else None
    has_yard = request.args.get("has_yard")
    has_pool = request.args.get("has_pool")
    has_solar = request.args.get("has_solar")
    max_age = request.args.get("max_age", type=int)
    sort_by = request.args.get("sort_by", "value_score")
    sort_dir = request.args.get("sort_dir", "desc")

    # Convert string booleans
    has_yard = has_yard.lower() == "true" if has_yard else None
    has_pool = has_pool.lower() == "true" if has_pool else None
    has_solar = has_solar.lower() == "true" if has_solar else None

    # Get filtered listings from database
    listings = database.get_filtered_listings(
        min_price=min_price,
        max_price=max_price,
        min_beds=min_beds,
        min_baths=min_baths,
        min_sqft=min_sqft,
        cities=cities,
        has_yard=has_yard,
        has_pool=has_pool,
        has_solar=has_solar,
        max_age=max_age,
    )

    # Sort listings
    reverse = sort_dir.lower() == "desc"

    if sort_by and listings:
        try:
            listings.sort(
                key=lambda l: getattr(l, sort_by) or 0,
                reverse=reverse
            )
        except AttributeError:
            logger.warning(f"Invalid sort field: {sort_by}")

    # Convert to dict for JSON
    results = [l.to_dict() for l in listings]

    # Log search
    database.log_search({
        "min_price": min_price,
        "max_price": max_price,
        "min_beds": min_beds,
        "cities": cities,
    }, len(results))

    return jsonify({
        "success": True,
        "count": len(results),
        "listings": results,
    })


@api.route("/listings/<listing_id>", methods=["GET"])
def get_listing(listing_id: str):
    """Get a single listing by ID with score breakdown."""
    listing = database.get_listing_by_id(listing_id)

    if not listing:
        return jsonify({"success": False, "error": "Listing not found"}), 404

    # Get all listings for score breakdown context
    all_listings = database.get_all_listings()
    breakdown = get_score_breakdown(listing, all_listings)

    return jsonify({
        "success": True,
        "listing": listing.to_dict(),
        "score_breakdown": breakdown,
    })


@api.route("/refresh", methods=["POST"])
def refresh_data():
    """
    Trigger a data refresh from Redfin.
    This will fetch new listings, enrich them, and calculate scores.
    """
    try:
        logger.info("Starting data refresh...")

        # Fetch new listings
        listings = fetch_listings()

        if not listings:
            return jsonify({
                "success": False,
                "error": "No listings fetched. The scraper may be blocked or no listings match criteria.",
            }), 500

        # Enrich listings with additional data
        enriched = enrich_all_listings(listings)

        # Calculate value scores
        scored = score_all_listings(enriched)

        # Clear old data and save new
        database.delete_all_listings()
        database.save_listings(scored)

        return jsonify({
            "success": True,
            "message": f"Refreshed {len(scored)} listings",
            "count": len(scored),
        })

    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@api.route("/filters", methods=["GET"])
def get_filters():
    """Get available filter options based on current data."""
    listings = database.get_all_listings()

    # Collect unique values
    cities = sorted(set(l.city for l in listings if l.city))
    property_types = sorted(set(l.property_type for l in listings if l.property_type))

    # Get ranges
    prices = [l.price for l in listings if l.price]
    sqfts = [l.sqft for l in listings if l.sqft]
    years = [l.year_built for l in listings if l.year_built]

    return jsonify({
        "success": True,
        "filters": {
            "cities": cities,
            "property_types": property_types,
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
            },
            "sqft_range": {
                "min": min(sqfts) if sqfts else 0,
                "max": max(sqfts) if sqfts else 0,
            },
            "year_range": {
                "min": min(years) if years else 0,
                "max": max(years) if years else 0,
            },
            "defaults": {
                "min_price": config.PRICE_RANGE[0],
                "max_price": config.PRICE_RANGE[1],
                "min_beds": config.MIN_BEDS,
                "min_baths": config.MIN_BATHS,
                "min_sqft": config.MIN_SQFT,
            },
        },
    })


@api.route("/stats", methods=["GET"])
def get_stats():
    """Get summary statistics about current listings."""
    listings = database.get_all_listings()

    if not listings:
        return jsonify({
            "success": True,
            "stats": {
                "total_listings": 0,
                "message": "No listings in database. Click Refresh to fetch data.",
            },
        })

    # Calculate stats
    prices = [l.price for l in listings if l.price]
    scores = [l.value_score for l in listings if l.value_score]

    # Count by city
    cities = {}
    for l in listings:
        cities[l.city] = cities.get(l.city, 0) + 1

    # Count features
    with_pool = sum(1 for l in listings if l.has_pool)
    with_yard = sum(1 for l in listings if l.has_yard)
    with_solar = sum(1 for l in listings if l.has_solar)

    return jsonify({
        "success": True,
        "stats": {
            "total_listings": len(listings),
            "price": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "avg": round(sum(prices) / len(prices)) if prices else 0,
            },
            "value_score": {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "avg": round(sum(scores) / len(scores), 1) if scores else 0,
            },
            "by_city": cities,
            "features": {
                "with_pool": with_pool,
                "with_yard": with_yard,
                "with_solar": with_solar,
            },
        },
    })


@api.route("/export", methods=["GET"])
def export_csv():
    """Export listings to CSV format."""
    from flask import Response
    import csv
    import io

    listings = database.get_all_listings()

    # Sort by value score
    listings.sort(key=lambda l: l.value_score or 0, reverse=True)

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Address", "City", "Price", "Beds", "Baths", "SqFt", "Year Built",
        "Lot SqFt", "HOA/Month", "Annual Tax", "Days on Market",
        "Has Pool", "Has Yard", "Has Solar", "Crime Index",
        "Distance to Downtown", "Nearest Downtown", "Value Score", "URL"
    ])

    # Data rows
    for l in listings:
        writer.writerow([
            l.address, l.city, l.price, l.beds, l.baths, l.sqft, l.year_built,
            l.lot_sqft, l.hoa_monthly, l.annual_tax, l.days_on_market,
            "Yes" if l.has_pool else "No",
            "Yes" if l.has_yard else "No",
            "Yes" if l.has_solar else "No",
            l.crime_index, l.distance_to_downtown, l.nearest_downtown,
            l.value_score, l.url
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=listings.csv"}
    )
