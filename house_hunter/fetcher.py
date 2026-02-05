"""Data fetcher for retrieving real estate listings from Redfin API."""

import json
import time
import logging
from typing import List, Optional
from datetime import datetime

import requests

from .models import Listing
from . import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedfinFetcher:
    """Fetches listings from Redfin via their stingray API."""

    BASE_URL = "https://www.redfin.com"
    API_URL = "https://www.redfin.com/stingray/api/gis"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.redfin.com/",
        })

    def fetch_city_listings(self, city: str) -> List[Listing]:
        """Fetch all listings for a single city using the Redfin API."""
        region_info = config.REDFIN_REGIONS.get(city)
        if not region_info:
            logger.warning(f"No region info for city: {city}")
            return []

        logger.info(f"Fetching listings for {city} (region_id: {region_info['id']})")

        # Build API parameters
        params = {
            "al": 1,
            "include_nearby_homes": "true",
            "num_homes": 350,  # Max results per request
            "ord": "redfin-recommended-asc",
            "page_number": 1,
            "region_id": region_info["id"],
            "region_type": 6,  # 6 = City
            "sf": "1,2,3,5,6,7",
            "status": 9,  # For sale
            "uipt": "1,2",  # 1=House, 2=Townhouse (no condos)
            "v": 8,
        }

        try:
            response = self.session.get(self.API_URL, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {city}: {e}")
            return []

        # Parse the response (Redfin returns {}&&{json})
        text = response.text
        if text.startswith("{}&&"):
            text = text[4:]

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for {city}: {e}")
            return []

        # Check for errors
        if data.get("resultCode") != 0:
            logger.warning(f"API error for {city}: {data.get('errorMessage')}")
            return []

        # Extract homes from payload
        payload = data.get("payload", {})
        homes = payload.get("homes", [])

        logger.info(f"API returned {len(homes)} homes for {city}")

        # Parse each home into a Listing
        listings = []
        for home in homes:
            listing = self._parse_home_data(home, city)
            if listing and listing.passes_hard_filters():
                listings.append(listing)

        logger.info(f"Found {len(listings)} valid listings in {city} (after filters)")
        return listings

    def _extract_value(self, obj, default=None):
        """Extract value from Redfin's nested {value: x, level: y} structure."""
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get("value", default)
        return obj

    def _parse_home_data(self, home: dict, city: str) -> Optional[Listing]:
        """Parse a single home from API response into a Listing object."""
        try:
            # Extract ID
            listing_id = str(home.get("listingId") or home.get("propertyId") or "")
            if not listing_id:
                mls_id = home.get("mlsId", {})
                listing_id = str(self._extract_value(mls_id) or f"rf_{hash(str(home))}")

            # Extract address - handle nested {value: x, level: y} structure
            street_line_raw = home.get("streetLine")
            if isinstance(street_line_raw, dict):
                street_line = street_line_raw.get("value", "")
            else:
                street_line = street_line_raw or ""

            # Extract location
            home_city = home.get("city", city)
            state = home.get("state", "AZ")
            zip_code = home.get("zip") or home.get("postalCode", "")

            # Extract price
            price = self._extract_value(home.get("price"), 0)
            price = int(price) if price else 0

            # Basic details
            beds = home.get("beds")
            beds = int(beds) if beds else 0

            baths = home.get("baths")
            baths = float(baths) if baths else 0.0

            sqft = self._extract_value(home.get("sqFt"), 0)
            sqft = int(sqft) if sqft else 0

            # Year built
            year_built = self._extract_value(home.get("yearBuilt"))
            year_built = int(year_built) if year_built else None

            # Lot size
            lot_size = self._extract_value(home.get("lotSize"))
            lot_sqft = int(lot_size) if lot_size else None

            # HOA
            hoa = self._extract_value(home.get("hoa"))
            hoa_monthly = int(hoa) if hoa else None

            # Days on market
            dom = self._extract_value(home.get("dom"))
            if dom is None:
                dom = self._extract_value(home.get("timeOnRedfin"))
            days_on_market = int(dom) if dom else None

            # Property type (use uiPropertyType which is the user-facing classification)
            prop_type_code = home.get("uiPropertyType")
            prop_type = self._map_property_type(prop_type_code)

            # Number of stories
            stories = self._extract_value(home.get("stories"))
            stories = int(stories) if stories else None

            # URL
            url_path = home.get("url", "")
            if url_path and not url_path.startswith("http"):
                url_path = f"{self.BASE_URL}{url_path}"

            # Coordinates
            lat_long = home.get("latLong", {})
            latitude = lat_long.get("latitude") if isinstance(lat_long, dict) else None
            longitude = lat_long.get("longitude") if isinstance(lat_long, dict) else None

            # Features detection from listing remarks and key facts
            remarks = home.get("listingRemarks", "") or ""
            remarks_lower = remarks.lower()
            key_facts = home.get("keyFacts", []) or []
            key_facts_str = " ".join(str(f) for f in key_facts).lower()

            has_pool = "pool" in remarks_lower or "pool" in key_facts_str or home.get("skPoolType")
            has_solar = "solar" in remarks_lower or "solar" in key_facts_str
            has_garage = "garage" in remarks_lower or "garage" in key_facts_str

            # Yard detection (lot size > 3000 sqft or mentioned in remarks)
            has_yard = (lot_sqft and lot_sqft > 3000) or "yard" in remarks_lower

            # Photo URL
            photos = home.get("photos", [])
            photo_url = None
            if photos and isinstance(photos, list) and len(photos) > 0:
                photo_url = photos[0] if isinstance(photos[0], str) else None

            listing = Listing(
                id=listing_id,
                source="redfin",
                url=url_path,
                address=street_line,
                city=home_city,
                state=state,
                zip_code=str(zip_code),
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                price=price,
                beds=beds,
                baths=baths,
                sqft=sqft,
                lot_sqft=lot_sqft,
                year_built=year_built,
                property_type=prop_type,
                stories=stories,
                hoa_monthly=hoa_monthly,
                days_on_market=days_on_market,
                has_pool=bool(has_pool),
                has_yard=bool(has_yard),
                has_solar=bool(has_solar),
                has_garage=bool(has_garage),
                photo_url=photo_url,
                description=remarks,
            )

            return listing

        except Exception as e:
            logger.debug(f"Failed to parse home data: {e}")
            return None

    def _map_property_type(self, code) -> str:
        """Map Redfin uiPropertyType codes to readable names."""
        type_map = {
            1: "single_family",
            2: "townhouse",
            3: "condo",
            4: "multi_family",
            5: "land",
            6: "manufactured",
            7: "other",
            8: "apartment",
        }
        return type_map.get(code, "unknown")

    def fetch_all_listings(self) -> List[Listing]:
        """Fetch listings for all configured cities."""
        all_listings = []
        seen_ids = set()

        for city in config.REDFIN_REGIONS.keys():
            listings = self.fetch_city_listings(city)

            # Deduplicate by listing ID
            for listing in listings:
                if listing.id not in seen_ids:
                    seen_ids.add(listing.id)
                    all_listings.append(listing)

            # Rate limiting between cities
            time.sleep(config.REQUEST_DELAY_SECONDS)

        logger.info(f"Total unique listings fetched: {len(all_listings)}")
        return all_listings


def fetch_listings() -> List[Listing]:
    """Main entry point for fetching listings."""
    fetcher = RedfinFetcher()
    return fetcher.fetch_all_listings()
