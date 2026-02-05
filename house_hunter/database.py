"""SQLite database operations for storing listings and cache."""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models import Listing
from . import config


def get_db_path() -> Path:
    """Get the database file path, creating directory if needed."""
    db_path = Path(config.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Main listings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            url TEXT,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT DEFAULT 'AZ',
            zip_code TEXT,
            latitude REAL,
            longitude REAL,
            price INTEGER,
            beds INTEGER,
            baths REAL,
            sqft INTEGER,
            lot_sqft INTEGER,
            year_built INTEGER,
            property_type TEXT,
            stories INTEGER,
            hoa_monthly INTEGER,
            annual_tax INTEGER,
            days_on_market INTEGER,
            list_date TEXT,
            has_pool BOOLEAN DEFAULT 0,
            has_yard BOOLEAN DEFAULT 0,
            has_solar BOOLEAN DEFAULT 0,
            has_garage BOOLEAN DEFAULT 0,
            has_basement BOOLEAN DEFAULT 0,
            garage_spaces INTEGER DEFAULT 0,
            walk_score INTEGER,
            crime_index INTEGER,
            distance_to_downtown REAL,
            nearest_downtown TEXT,
            value_score REAL,
            last_updated TEXT,
            photo_url TEXT,
            description TEXT
        )
    """)

    # Enrichment cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_cache (
            address TEXT PRIMARY KEY,
            walk_score INTEGER,
            latitude REAL,
            longitude REAL,
            cached_at TEXT
        )
    """)

    # Search history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_params TEXT,
            results_count INTEGER,
            searched_at TEXT
        )
    """)

    # Create indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_city ON listings(city)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_value_score ON listings(value_score)")

    # Migration: Add stories column if it doesn't exist
    cursor.execute("PRAGMA table_info(listings)")
    columns = [row[1] for row in cursor.fetchall()]
    if "stories" not in columns:
        cursor.execute("ALTER TABLE listings ADD COLUMN stories INTEGER")

    conn.commit()
    conn.close()


def save_listing(listing: Listing):
    """Save or update a single listing."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO listings (
            id, source, url, address, city, state, zip_code,
            latitude, longitude, price, beds, baths, sqft, lot_sqft,
            year_built, property_type, stories, hoa_monthly, annual_tax,
            days_on_market, list_date, has_pool, has_yard, has_solar,
            has_garage, has_basement, garage_spaces, walk_score,
            crime_index, distance_to_downtown, nearest_downtown,
            value_score, last_updated, photo_url, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        listing.id, listing.source, listing.url, listing.address,
        listing.city, listing.state, listing.zip_code, listing.latitude,
        listing.longitude, listing.price, listing.beds, listing.baths,
        listing.sqft, listing.lot_sqft, listing.year_built,
        listing.property_type, listing.stories, listing.hoa_monthly, listing.annual_tax,
        listing.days_on_market, listing.list_date, listing.has_pool,
        listing.has_yard, listing.has_solar, listing.has_garage,
        listing.has_basement, listing.garage_spaces, listing.walk_score,
        listing.crime_index, listing.distance_to_downtown,
        listing.nearest_downtown, listing.value_score, listing.last_updated,
        listing.photo_url, listing.description
    ))

    conn.commit()
    conn.close()


def save_listings(listings: List[Listing]):
    """Save multiple listings in a batch."""
    for listing in listings:
        save_listing(listing)


def get_all_listings() -> List[Listing]:
    """Retrieve all listings from the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM listings")
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_listing(row) for row in rows]


def get_filtered_listings(
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_beds: Optional[int] = None,
    min_baths: Optional[float] = None,
    min_sqft: Optional[int] = None,
    cities: Optional[List[str]] = None,
    has_yard: Optional[bool] = None,
    has_pool: Optional[bool] = None,
    has_solar: Optional[bool] = None,
    max_age: Optional[int] = None,
) -> List[Listing]:
    """Retrieve listings with optional filters applied."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM listings WHERE 1=1"
    params = []

    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)

    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)

    if min_beds is not None:
        query += " AND beds >= ?"
        params.append(min_beds)

    if min_baths is not None:
        query += " AND baths >= ?"
        params.append(min_baths)

    if min_sqft is not None:
        query += " AND sqft >= ?"
        params.append(min_sqft)

    if cities:
        placeholders = ",".join("?" * len(cities))
        query += f" AND city IN ({placeholders})"
        params.extend(cities)

    if has_yard is not None:
        query += " AND has_yard = ?"
        params.append(1 if has_yard else 0)

    if has_pool is not None:
        query += " AND has_pool = ?"
        params.append(1 if has_pool else 0)

    if has_solar is not None:
        query += " AND has_solar = ?"
        params.append(1 if has_solar else 0)

    if max_age is not None:
        min_year = datetime.now().year - max_age
        query += " AND year_built >= ?"
        params.append(min_year)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_listing(row) for row in rows]


def get_listing_by_id(listing_id: str) -> Optional[Listing]:
    """Retrieve a single listing by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
    row = cursor.fetchone()
    conn.close()

    return _row_to_listing(row) if row else None


def delete_all_listings():
    """Delete all listings from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM listings")
    conn.commit()
    conn.close()


def get_listing_count() -> int:
    """Get total number of listings in database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM listings")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def save_enrichment_cache(address: str, walk_score: Optional[int], lat: Optional[float], lon: Optional[float]):
    """Cache enrichment data for an address."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO enrichment_cache (address, walk_score, latitude, longitude, cached_at)
        VALUES (?, ?, ?, ?, ?)
    """, (address, walk_score, lat, lon, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_enrichment_cache(address: str) -> Optional[dict]:
    """Get cached enrichment data for an address."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM enrichment_cache WHERE address = ?", (address,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "walk_score": row["walk_score"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
    return None


def log_search(params: dict, results_count: int):
    """Log a search to history."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO search_history (search_params, results_count, searched_at)
        VALUES (?, ?, ?)
    """, (json.dumps(params), results_count, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def _row_to_listing(row: sqlite3.Row) -> Listing:
    """Convert a database row to a Listing object."""
    return Listing(
        id=row["id"],
        source=row["source"],
        url=row["url"] or "",
        address=row["address"],
        city=row["city"],
        state=row["state"] or "AZ",
        zip_code=row["zip_code"] or "",
        latitude=row["latitude"],
        longitude=row["longitude"],
        price=row["price"] or 0,
        beds=row["beds"] or 0,
        baths=row["baths"] or 0.0,
        sqft=row["sqft"] or 0,
        lot_sqft=row["lot_sqft"],
        year_built=row["year_built"],
        property_type=row["property_type"] or "",
        stories=row["stories"],
        hoa_monthly=row["hoa_monthly"],
        annual_tax=row["annual_tax"],
        days_on_market=row["days_on_market"],
        list_date=row["list_date"],
        has_pool=bool(row["has_pool"]),
        has_yard=bool(row["has_yard"]),
        has_solar=bool(row["has_solar"]),
        has_garage=bool(row["has_garage"]),
        has_basement=bool(row["has_basement"]),
        garage_spaces=row["garage_spaces"] or 0,
        walk_score=row["walk_score"],
        crime_index=row["crime_index"],
        distance_to_downtown=row["distance_to_downtown"],
        nearest_downtown=row["nearest_downtown"],
        value_score=row["value_score"],
        last_updated=row["last_updated"] or "",
        photo_url=row["photo_url"],
        description=row["description"],
    )
