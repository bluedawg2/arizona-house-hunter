# House Hunter Web App Conversion - Testing Plan

## Overview

Converting the House Hunter application from Flask + jQuery/DataTables to a modern, mobile-responsive web app using the frontend-design skill for a polished, production-grade UI.

---

## Current Architecture

| Layer | Current | Target |
|-------|---------|--------|
| Backend | Flask API | Streamlit or FastAPI |
| Frontend | jQuery + DataTables | Modern React-style components via frontend-design |
| Database | SQLite | SQLite (unchanged) |
| Styling | Custom CSS | Tailwind/modern CSS (mobile-first) |

---

## Testing Strategy

### Phase 1: Backend Verification (Pre-Conversion)

Ensure existing backend modules work correctly before UI conversion.

#### 1.1 Database Tests
- [ ] `database.init_database()` creates schema without errors
- [ ] `save_listing()` inserts a new listing
- [ ] `save_listing()` updates an existing listing (upsert)
- [ ] `get_all_listings()` returns correct count
- [ ] `get_filtered_listings()` respects all filter parameters:
  - [ ] Price range (min_price, max_price)
  - [ ] Bedrooms (min_beds)
  - [ ] Bathrooms (min_baths)
  - [ ] Square footage (min_sqft)
  - [ ] Cities filter (single and multiple)
  - [ ] Boolean features (has_yard, has_pool, has_solar)
  - [ ] Max age / year_built threshold
  - [ ] Sorting (sort_by, sort_dir)
- [ ] `delete_all_listings()` clears all data
- [ ] `log_search()` records search history

#### 1.2 Fetcher Tests
- [ ] `fetch_listings()` connects to Redfin API
- [ ] Listings are deduplicated by ID
- [ ] Rate limiting works (2.5s delay between cities)
- [ ] All 7 cities are queried
- [ ] Error handling for network failures

#### 1.3 Model Tests
- [ ] `Listing.passes_hard_filters()` correctly filters:
  - [ ] Rejects < 3 bedrooms
  - [ ] Rejects < 2 bathrooms
  - [ ] Rejects < 1,200 sqft
  - [ ] Rejects price outside $400k-$700k
  - [ ] Rejects homes older than 30 years
  - [ ] Rejects condos, apartments, manufactured homes
  - [ ] Accepts single-family and townhouse
- [ ] `Listing.to_dict()` serializes all fields
- [ ] `Listing.from_dict()` deserializes correctly

#### 1.4 Enrichment Tests
- [ ] Crime index lookup returns correct values per city
- [ ] Unknown cities default to 50
- [ ] Case-insensitive city matching
- [ ] Distance calculation is accurate (haversine)
- [ ] Nearest downtown identification works
- [ ] Yard inference from lot_sqft > 3000

#### 1.5 Scoring Tests
- [ ] Normalization produces values in [0, 1]
- [ ] Inverted normalization works (lower = better)
- [ ] Final scores are in [0, 100] range
- [ ] Better value properties score higher
- [ ] Weighted components sum correctly
- [ ] Edge cases: empty list, single listing

**Run existing tests:**
```bash
python -m pytest house_hunter/tests/ -v
```

---

### Phase 2: API/Integration Tests

Test the data flow end-to-end before UI changes.

#### 2.1 Full Pipeline Test
- [ ] Fetch → Filter → Enrich → Score → Save pipeline completes
- [ ] Listings in database have all enriched fields populated
- [ ] Value scores are calculated and stored

#### 2.2 Export Functionality
- [ ] CSV export includes all expected columns (19)
- [ ] CSV data matches database content
- [ ] Filtering applies to export

#### 2.3 Statistics Calculation
- [ ] Total count is accurate
- [ ] Price min/max/avg are correct
- [ ] City breakdown sums to total
- [ ] Feature counts are accurate

---

### Phase 3: UI Conversion Tests

After implementing the new frontend using frontend-design skill.

#### 3.1 Layout & Responsiveness
- [ ] **Desktop (1200px+):** Sidebar + main content layout
- [ ] **Tablet (768px-1199px):** Collapsible sidebar or top filters
- [ ] **Mobile (< 768px):** Stacked layout, hamburger menu for filters
- [ ] Filter panel is accessible on all screen sizes
- [ ] Data table/cards are readable on mobile
- [ ] Touch targets are at least 44x44px

#### 3.2 Filter UI
- [ ] Price range inputs accept valid numbers
- [ ] Price range validation (min < max)
- [ ] Bedroom/bathroom dropdowns work
- [ ] City checkboxes select/deselect properly
- [ ] "Select All" / "Deselect All" cities works
- [ ] Feature checkboxes toggle correctly
- [ ] Max age dropdown functions
- [ ] Apply Filters button triggers reload
- [ ] Reset Filters restores defaults
- [ ] Filters persist during session

#### 3.3 Data Display
- [ ] Listings load on page open
- [ ] Loading indicator shows during fetch
- [ ] Empty state message when no results
- [ ] Error message on fetch failure
- [ ] Listing count displays correctly
- [ ] Sorting works (click column headers)
- [ ] Default sort: value_score descending

#### 3.4 Listing Cards/Rows
- [ ] Address displays correctly
- [ ] Price formatted with commas ($XXX,XXX)
- [ ] Beds/baths/sqft display
- [ ] Year built shows
- [ ] City name visible
- [ ] Value score with color coding:
  - [ ] Green: 70+
  - [ ] Yellow: 50-69
  - [ ] Red: < 50
- [ ] Crime index with color coding
- [ ] Feature badges (pool, yard, solar)
- [ ] Click/tap opens detail view

#### 3.5 Detail View
- [ ] All property details display
- [ ] Photo displays (if available)
- [ ] Score breakdown shows all components
- [ ] Link to Redfin listing works
- [ ] Close/back button works
- [ ] Scrollable on mobile

#### 3.6 Refresh Data Flow
- [ ] Refresh button is prominent
- [ ] Confirmation dialog before refresh
- [ ] Progress indicator during fetch
- [ ] Status messages show current city being fetched
- [ ] Success message with count
- [ ] Error handling with retry option
- [ ] Data updates after completion

#### 3.7 Export Functionality
- [ ] Export button visible
- [ ] Downloads CSV file
- [ ] Filename includes date
- [ ] Respects current filters

---

### Phase 4: Mobile-Specific Tests

Critical for phone usage as requested.

#### 4.1 Touch Interactions
- [ ] Swipe gestures (if implemented)
- [ ] Pull-to-refresh (if implemented)
- [ ] Double-tap zoom disabled on inputs
- [ ] No horizontal scroll on any view
- [ ] Keyboard doesn't obscure inputs

#### 4.2 Performance
- [ ] Initial load < 3 seconds on 4G
- [ ] Filter changes respond < 500ms
- [ ] Smooth scrolling through listings
- [ ] Images lazy load

#### 4.3 Mobile Chrome/Safari
- [ ] Test on iOS Safari
- [ ] Test on Android Chrome
- [ ] Address bar auto-hides
- [ ] Viewport meta tag correct
- [ ] No flash of unstyled content

#### 4.4 Offline/Poor Connection
- [ ] Graceful error on network loss
- [ ] Cached data remains visible
- [ ] Retry mechanism available

---

### Phase 5: Accessibility Tests

#### 5.1 Basic A11y
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] Screen reader can navigate filters
- [ ] Data table/cards have proper labels
- [ ] Error messages announced

---

### Phase 6: Deployment Tests

#### 6.1 Streamlit Cloud (if using Streamlit)
- [ ] `requirements.txt` includes all dependencies
- [ ] App deploys without errors
- [ ] Environment variables configured
- [ ] Database persists (or uses external DB)

#### 6.2 Alternative Deployment
- [ ] Docker container builds
- [ ] Container runs correctly
- [ ] Port mapping works
- [ ] Health check endpoint responds

---

## Test Data Requirements

### Minimum Test Dataset
- At least 20 listings covering:
  - Multiple cities (Gilbert, Chandler, Scottsdale, Mesa, Tucson)
  - Price range spread ($400k to $700k)
  - Various scores (high, medium, low)
  - Mix of features (with/without pool, yard, solar)
  - Different ages (new and 25+ years)

### Edge Cases
- Listing with missing optional fields
- Listing at exact filter boundaries
- City with no listings
- Very long address text
- Special characters in description

---

## Testing Commands

```bash
# Run all unit tests
python -m pytest house_hunter/tests/ -v

# Run with coverage
python -m pytest house_hunter/tests/ --cov=house_hunter --cov-report=html

# Test database operations
python -c "from house_hunter.database import init_database; init_database(); print('DB OK')"

# Test fetcher (single city, limited)
python -c "from house_hunter.fetcher import fetch_listings; print(len(fetch_listings()))"

# Manual smoke test
# 1. Start app
# 2. Verify listings load
# 3. Apply a filter
# 4. Click a listing
# 5. Export CSV
# 6. Refresh data
```

---

## Success Criteria

### Must Have
- [ ] All backend unit tests pass
- [ ] Listings display correctly on desktop and mobile
- [ ] Filters work correctly
- [ ] Detail view accessible
- [ ] Export works
- [ ] Refresh fetches new data

### Should Have
- [ ] Responsive design works on phone
- [ ] Touch-friendly interface
- [ ] Fast load times
- [ ] Accessible UI

### Nice to Have
- [ ] Offline support
- [ ] Push notifications for new listings
- [ ] Saved searches

---

## Next Steps

1. **Run existing tests** to verify backend is stable
2. **Use frontend-design skill** to create mobile-first UI
3. **Implement new frontend** with Streamlit or modern framework
4. **Execute test plan** phase by phase
5. **Deploy** to Streamlit Cloud or chosen platform
