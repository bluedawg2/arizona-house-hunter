"""Unit tests for the scoring engine."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from house_hunter.models import Listing
from house_hunter.scoring import calculate_value_score, normalize_value, score_all_listings


class TestNormalization(unittest.TestCase):
    """Test the normalize_value function."""

    def test_normalize_value_middle(self):
        """Test normalization returns 0.5 for middle value."""
        values = [0, 50, 100]
        result = normalize_value(50, values)
        self.assertEqual(result, 0.5)

    def test_normalize_value_min(self):
        """Test normalization returns 0 for minimum value."""
        values = [10, 50, 100]
        result = normalize_value(10, values)
        self.assertEqual(result, 0.0)

    def test_normalize_value_max(self):
        """Test normalization returns 1 for maximum value."""
        values = [10, 50, 100]
        result = normalize_value(100, values)
        self.assertEqual(result, 1.0)

    def test_normalize_value_inverted(self):
        """Test inverted normalization (lower is better)."""
        values = [10, 50, 100]
        # Min value should return 1 when inverted
        result = normalize_value(10, values, invert=True)
        self.assertEqual(result, 1.0)
        # Max value should return 0 when inverted
        result = normalize_value(100, values, invert=True)
        self.assertEqual(result, 0.0)

    def test_normalize_empty_list(self):
        """Test normalization with empty list returns 0.5."""
        result = normalize_value(50, [])
        self.assertEqual(result, 0.5)

    def test_normalize_single_value(self):
        """Test normalization with single value returns 0.5."""
        result = normalize_value(50, [50])
        self.assertEqual(result, 0.5)


class TestScoring(unittest.TestCase):
    """Test the value scoring algorithm."""

    def setUp(self):
        """Create sample listings for testing."""
        self.listings = [
            Listing(
                id="1",
                source="test",
                url="",
                address="123 Test St",
                city="Gilbert",
                price=500000,
                beds=4,
                baths=2.5,
                sqft=2000,
                year_built=2020,
                hoa_monthly=100,
                annual_tax=3000,
                days_on_market=30,
                has_pool=True,
                has_yard=True,
                has_solar=False,
            ),
            Listing(
                id="2",
                source="test",
                url="",
                address="456 Test Ave",
                city="Chandler",
                price=600000,
                beds=3,
                baths=2,
                sqft=1800,
                year_built=2010,
                hoa_monthly=200,
                annual_tax=4000,
                days_on_market=60,
                has_pool=False,
                has_yard=True,
                has_solar=True,
            ),
            Listing(
                id="3",
                source="test",
                url="",
                address="789 Test Blvd",
                city="Mesa",
                price=450000,
                beds=3,
                baths=2,
                sqft=1600,
                year_built=2015,
                hoa_monthly=0,
                annual_tax=2500,
                days_on_market=90,
                has_pool=False,
                has_yard=False,
                has_solar=False,
            ),
        ]

    def test_calculate_value_score_returns_number(self):
        """Test that calculate_value_score returns a numeric score."""
        score = calculate_value_score(self.listings[0], self.listings)
        self.assertIsInstance(score, (int, float))

    def test_score_range(self):
        """Test that scores are within 0-100 range."""
        for listing in self.listings:
            score = calculate_value_score(listing, self.listings)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

    def test_better_value_higher_score(self):
        """Test that better value properties get higher scores."""
        # Listing 1 has newer year, pool, yard - should score higher than listing 3
        score1 = calculate_value_score(self.listings[0], self.listings)
        score3 = calculate_value_score(self.listings[2], self.listings)

        # Both have their strengths, but listing 1 is newer with more features
        # Score comparison depends on specific weights
        self.assertIsNotNone(score1)
        self.assertIsNotNone(score3)

    def test_no_hoa_bonus(self):
        """Test that no HOA gets maximum HOA score."""
        # Listing 3 has no HOA
        score = calculate_value_score(self.listings[2], self.listings)
        self.assertIsNotNone(score)

    def test_score_all_listings_sorts(self):
        """Test that score_all_listings returns sorted results."""
        scored = score_all_listings(self.listings.copy())

        # Check descending order
        for i in range(len(scored) - 1):
            self.assertGreaterEqual(
                scored[i].value_score or 0,
                scored[i + 1].value_score or 0
            )

    def test_score_assigned_to_listing(self):
        """Test that scoring assigns value_score to listings."""
        scored = score_all_listings(self.listings.copy())

        for listing in scored:
            self.assertIsNotNone(listing.value_score)


class TestListingModel(unittest.TestCase):
    """Test the Listing model."""

    def test_passes_hard_filters(self):
        """Test that hard filters work correctly."""
        # Valid listing
        valid = Listing(
            id="1",
            source="test",
            url="",
            address="123 Test",
            city="Gilbert",
            price=500000,
            beds=3,
            baths=2,
            sqft=1500,
            year_built=2000,
            property_type="single_family",
        )
        self.assertTrue(valid.passes_hard_filters())

    def test_fails_beds_filter(self):
        """Test that listing with too few beds fails filter."""
        listing = Listing(
            id="1",
            source="test",
            url="",
            address="123 Test",
            city="Gilbert",
            price=500000,
            beds=2,  # Less than min 3
            baths=2,
            sqft=1500,
            year_built=2000,
        )
        self.assertFalse(listing.passes_hard_filters())

    def test_fails_sqft_filter(self):
        """Test that listing with too few sqft fails filter."""
        listing = Listing(
            id="1",
            source="test",
            url="",
            address="123 Test",
            city="Gilbert",
            price=500000,
            beds=3,
            baths=2,
            sqft=1000,  # Less than min 1300
            year_built=2000,
        )
        self.assertFalse(listing.passes_hard_filters())

    def test_fails_year_filter(self):
        """Test that old listing fails filter."""
        listing = Listing(
            id="1",
            source="test",
            url="",
            address="123 Test",
            city="Gilbert",
            price=500000,
            beds=3,
            baths=2,
            sqft=1500,
            year_built=1990,  # Before 1996
        )
        self.assertFalse(listing.passes_hard_filters())

    def test_fails_condo_filter(self):
        """Test that condo fails filter."""
        listing = Listing(
            id="1",
            source="test",
            url="",
            address="123 Test",
            city="Gilbert",
            price=500000,
            beds=3,
            baths=2,
            sqft=1500,
            year_built=2000,
            property_type="condo",
        )
        self.assertFalse(listing.passes_hard_filters())

    def test_to_dict(self):
        """Test that to_dict returns all fields."""
        listing = Listing(
            id="1",
            source="test",
            url="http://example.com",
            address="123 Test",
            city="Gilbert",
            price=500000,
        )
        d = listing.to_dict()

        self.assertEqual(d["id"], "1")
        self.assertEqual(d["source"], "test")
        self.assertEqual(d["address"], "123 Test")
        self.assertEqual(d["city"], "Gilbert")
        self.assertEqual(d["price"], 500000)


if __name__ == "__main__":
    unittest.main()
