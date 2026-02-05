"""Unit tests for the enrichment module."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from house_hunter.models import Listing
from house_hunter.enrichment import (
    get_crime_index,
    GeoEnricher,
)


class TestCrimeIndex(unittest.TestCase):
    """Test crime index lookup."""

    def test_gilbert_safe(self):
        """Test Gilbert has high safety score."""
        score = get_crime_index("Gilbert")
        self.assertEqual(score, 85)

    def test_tucson_lower(self):
        """Test Tucson has lower safety score."""
        score = get_crime_index("Tucson")
        self.assertEqual(score, 45)

    def test_unknown_city_default(self):
        """Test unknown city returns default score."""
        score = get_crime_index("Unknown City")
        self.assertEqual(score, 50)

    def test_case_insensitive(self):
        """Test city lookup is case normalized."""
        score = get_crime_index("gilbert")
        self.assertEqual(score, 85)

    def test_green_valley(self):
        """Test Green Valley lookup with space."""
        score = get_crime_index("Green Valley")
        self.assertEqual(score, 80)


class TestGeoEnricher(unittest.TestCase):
    """Test geographic enrichment functions."""

    def setUp(self):
        self.enricher = GeoEnricher()

    def test_calculate_distance_same_point(self):
        """Test distance between same point is 0."""
        distance = self.enricher.calculate_distance(
            33.4484, -112.0740,
            33.4484, -112.0740
        )
        self.assertEqual(distance, 0)

    def test_calculate_distance_phoenix_to_tucson(self):
        """Test distance between Phoenix and Tucson is approximately 100 miles."""
        # Phoenix: 33.4484, -112.0740
        # Tucson: 32.2226, -110.9747
        distance = self.enricher.calculate_distance(
            33.4484, -112.0740,
            32.2226, -110.9747
        )
        # Should be approximately 100-120 miles
        self.assertGreater(distance, 90)
        self.assertLess(distance, 130)

    def test_get_nearest_downtown_phoenix_area(self):
        """Test nearest downtown for Phoenix area location."""
        # Gilbert coordinates
        nearest, distance = self.enricher.get_nearest_downtown(
            33.3528, -111.7890
        )
        self.assertEqual(nearest, "Gilbert")
        self.assertLess(distance, 5)  # Should be very close

    def test_get_nearest_downtown_tucson_area(self):
        """Test nearest downtown for Tucson area location."""
        # Tucson coordinates
        nearest, distance = self.enricher.get_nearest_downtown(
            32.2226, -110.9747
        )
        self.assertEqual(nearest, "Tucson")
        self.assertLess(distance, 1)  # Should be essentially 0


class TestListingEnrichment(unittest.TestCase):
    """Test listing enrichment functionality."""

    @classmethod
    def setUpClass(cls):
        """Initialize database for tests."""
        from house_hunter import database
        database.init_database()

    def test_yard_inference_from_lot_size(self):
        """Test that yard is inferred from lot size."""
        listing = Listing(
            id="1",
            source="test",
            url="",
            address="123 Test",
            city="Gilbert",
            lot_sqft=5000,
            has_yard=False,
        )

        # After enrichment, has_yard should be True for lot > 3000
        from house_hunter.enrichment import enrich_listing
        enriched = enrich_listing(listing)
        self.assertTrue(enriched.has_yard)

    def test_small_lot_no_yard(self):
        """Test that small lot doesn't imply yard."""
        listing = Listing(
            id="1",
            source="test",
            url="",
            address="123 Test",
            city="Gilbert",
            lot_sqft=2000,
            has_yard=False,
        )

        from house_hunter.enrichment import enrich_listing
        enriched = enrich_listing(listing)
        self.assertFalse(enriched.has_yard)

    def test_crime_index_assigned(self):
        """Test that crime index is assigned based on city."""
        listing = Listing(
            id="1",
            source="test",
            url="",
            address="123 Test",
            city="Gilbert",
        )

        from house_hunter.enrichment import enrich_listing
        enriched = enrich_listing(listing)
        self.assertEqual(enriched.crime_index, 85)


if __name__ == "__main__":
    unittest.main()
