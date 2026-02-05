"""
Arizona House Hunter - Streamlit Web App
Mobile-friendly real estate listing analysis for Phoenix & Tucson metro areas.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import backend modules
from house_hunter import database, config
from house_hunter.models import Listing
from house_hunter.fetcher import fetch_listings
from house_hunter.enrichment import enrich_listing
from house_hunter.scoring import score_all_listings

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Arizona House Hunter",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark mode CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #1a1a1a;
        --bg-secondary: #242424;
        --bg-card: #2a2a2a;
        --text-primary: #f0f0f0;
        --text-secondary: #a0a0a0;
        --accent: #C4704B;
        --accent-light: #e8a889;
        --success: #4ade80;
        --warning: #fbbf24;
    }

    .stApp {
        background-color: var(--bg-primary);
    }

    #MainMenu, footer, header {visibility: hidden;}

    /* Stats row */
    .stats-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .stat-box {
        background: var(--bg-card);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        flex: 1;
        text-align: center;
    }
    .stat-box .value {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .stat-box .label {
        font-size: 0.7rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Compact listing card */
    .compact-card {
        background: var(--bg-card);
        border-radius: 10px;
        padding: 0.75rem;
        height: 100%;
        border: 1px solid #333;
        transition: border-color 0.2s;
    }
    .compact-card:hover {
        border-color: var(--accent);
    }

    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .score-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .score-high { background: #166534; color: #bbf7d0; }
    .score-mid { background: #854d0e; color: #fef08a; }
    .score-low { background: #7f1d1d; color: #fecaca; }

    .card-price {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .card-price.ideal { color: var(--success); }

    .card-address {
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 2px;
    }
    .card-city {
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }

    .card-specs {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-bottom: 0.5rem;
    }
    .spec-tag {
        background: var(--bg-secondary);
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        color: var(--text-secondary);
    }
    .spec-tag strong {
        color: var(--text-primary);
    }

    .card-features {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
    }
    .feature-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--accent);
    }
    .feature-text {
        font-size: 0.7rem;
        color: var(--text-secondary);
    }

    /* Override Streamlit defaults for dark mode */
    .stSelectbox label, .stMultiSelect label, .stNumberInput label, .stCheckbox label {
        color: var(--text-primary) !important;
    }

    .stButton > button {
        background: var(--accent) !important;
        color: #1a1a1a !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background: var(--accent-light) !important;
        color: #1a1a1a !important;
    }

    /* Link buttons */
    .stLinkButton > a {
        background: var(--accent) !important;
        color: #1a1a1a !important;
        border-radius: 8px !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid #444 !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }

    /* Sidebar dark */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary);
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'listings' not in st.session_state:
        st.session_state.listings = []
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None


def load_listings_from_db():
    """Load listings from database."""
    database.init_database()
    listings = database.get_all_listings()
    st.session_state.listings = listings
    return listings


def refresh_data():
    """Fetch fresh data from Redfin API with progress tracking."""
    import time
    from house_hunter.fetcher import RedfinFetcher
    from house_hunter import config as hh_config

    all_listings = []
    seen_ids = set()
    cities = list(hh_config.REDFIN_REGIONS.keys())

    # Progress UI
    progress_bar = st.progress(0)
    status_text = st.empty()

    fetcher = RedfinFetcher()
    total_steps = len(cities) + 2  # cities + enrich + score

    # Fetch from each city
    for i, city in enumerate(cities):
        progress_bar.progress(i / total_steps)
        status_text.text(f"📍 Fetching {city}... ({i+1}/{len(cities)})")

        try:
            listings = fetcher.fetch_city_listings(city)
            for listing in listings:
                if listing.id not in seen_ids:
                    seen_ids.add(listing.id)
                    all_listings.append(listing)
            status_text.text(f"✓ {city}: {len(listings)} homes ({len(all_listings)} total)")
        except Exception as e:
            status_text.text(f"⚠ {city}: {str(e)[:40]}")

        if i < len(cities) - 1:
            time.sleep(1.5)

    if not all_listings:
        progress_bar.empty()
        status_text.empty()
        st.error("No listings fetched. Redfin may be unavailable.")
        return

    # Enrich with progress
    from house_hunter.enrichment import GeoEnricher
    geo_enricher = GeoEnricher()  # Shared instance

    enriched = []
    enrich_container = st.empty()

    for i, listing in enumerate(all_listings):
        # Update progress display
        pct = int((i + 1) / len(all_listings) * 100)
        enrich_container.markdown(f"""
        <div style="background: #242424; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #a0a0a0;">🔍 Enriching listings...</span>
                <span style="color: #f0f0f0; font-weight: 600;">{i+1} / {len(all_listings)}</span>
            </div>
            <div style="background: #333; border-radius: 4px; height: 8px; overflow: hidden;">
                <div style="background: #C4704B; height: 100%; width: {pct}%; transition: width 0.1s;"></div>
            </div>
            <div style="color: #666; font-size: 0.8rem; margin-top: 0.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {listing.address[:40]}{'...' if len(listing.address) > 40 else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            enriched_listing = enrich_listing(listing, geo_enricher)
            enriched.append(enriched_listing)
        except:
            enriched.append(listing)

    enrich_container.empty()

    # Score
    status_text.text("📊 Calculating value scores...")
    progress_bar.progress((len(cities) + 1) / total_steps)
    scored = score_all_listings(enriched)

    # Save
    status_text.text("💾 Saving...")
    progress_bar.progress(1.0)
    database.delete_all_listings()
    database.save_listings(scored)

    st.session_state.listings = scored
    st.session_state.last_refresh = datetime.now()

    progress_bar.empty()
    status_text.empty()
    st.success(f"✓ Loaded {len(scored)} listings!")
    time.sleep(1)
    st.rerun()


def get_score_class(score):
    if not score:
        return "score-low"
    if score >= 55:
        return "score-high"
    if score >= 40:
        return "score-mid"
    return "score-low"


def format_price(price):
    if not price:
        return "--"
    return f"${price:,.0f}"


def format_compact_price(price):
    if not price:
        return "--"
    if price >= 1000000:
        return f"${price/1000000:.1f}M"
    return f"${price/1000:.0f}K"


def render_compact_card(listing: Listing):
    """Render a compact listing card."""
    score_class = get_score_class(listing.value_score)
    price_class = "ideal" if listing.price and listing.price <= 600000 else ""

    features = []
    if listing.has_pool:
        features.append("Pool")
    if listing.has_yard:
        features.append("Yard")
    if listing.has_solar:
        features.append("Solar")

    features_html = " ".join([f'<span class="feature-dot" title="{f}"></span>' for f in features])
    if features:
        features_html += f' <span class="feature-text">{", ".join(features)}</span>'

    return f"""
    <div class="compact-card">
        <div class="card-top">
            <span class="score-pill {score_class}">{listing.value_score or '--'}</span>
            <span class="card-price {price_class}">{format_compact_price(listing.price)}</span>
        </div>
        <div class="card-address">{listing.address}</div>
        <div class="card-city">{listing.city} · {listing.year_built or 'N/A'}</div>
        <div class="card-specs">
            <span class="spec-tag"><strong>{listing.beds}</strong> bd</span>
            <span class="spec-tag"><strong>{listing.baths}</strong> ba</span>
            <span class="spec-tag"><strong>{listing.sqft:,}</strong> sqft</span>
            <span class="spec-tag">${int(listing.price/listing.sqft) if listing.sqft else '--'}/ft</span>
        </div>
        <div class="card-features">{features_html}</div>
    </div>
    """


def filter_listings(listings, filters):
    """Filter listings based on user selections."""
    filtered = []
    for l in listings:
        if filters['min_price'] and l.price and l.price < filters['min_price']:
            continue
        if filters['max_price'] and l.price and l.price > filters['max_price']:
            continue
        if filters['min_beds'] and l.beds and l.beds < filters['min_beds']:
            continue
        if filters['min_baths'] and l.baths and l.baths < filters['min_baths']:
            continue
        if filters['min_sqft'] and l.sqft and l.sqft < filters['min_sqft']:
            continue
        if filters['cities'] and l.city not in filters['cities']:
            continue
        if filters['has_yard'] and not l.has_yard:
            continue
        if filters['has_pool'] and not l.has_pool:
            continue
        if filters['has_solar'] and not l.has_solar:
            continue
        if filters['max_age']:
            current_year = datetime.now().year
            if l.year_built and (current_year - l.year_built) > filters['max_age']:
                continue
        filtered.append(l)
    return filtered


def sort_listings(listings, sort_by):
    """Sort listings by specified field."""
    sort_config = {
        "Value Score": (lambda x: x.value_score or 0, True),
        "Price ↑": (lambda x: x.price or 0, False),
        "Price ↓": (lambda x: x.price or 0, True),
        "Largest": (lambda x: x.sqft or 0, True),
        "Newest": (lambda x: x.year_built or 0, True),
    }
    key_func, reverse = sort_config.get(sort_by, (lambda x: x.value_score or 0, True))
    return sorted(listings, key=key_func, reverse=reverse)


def main():
    """Main application."""
    init_session_state()

    # Header
    st.markdown("## 🏠 Arizona House Hunter")

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")

        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Min $", value=400000, step=25000, format="%d")
        with col2:
            max_price = st.number_input("Max $", value=700000, step=25000, format="%d")

        col1, col2 = st.columns(2)
        with col1:
            min_beds = st.selectbox("Beds", options=[1, 2, 3, 4, 5], index=2)
        with col2:
            min_baths = st.selectbox("Baths", options=[1, 1.5, 2, 2.5, 3, 3.5, 4], index=2)

        min_sqft = st.number_input("Min Sqft", value=1200, step=100, format="%d")

        all_cities = ['Gilbert', 'Chandler', 'Scottsdale', 'Mesa', 'Queen Creek',
                      'Apache Junction', 'Tucson', 'Green Valley', 'Oro Valley', 'Marana', 'Vail']
        default_cities = ['Gilbert', 'Chandler', 'Scottsdale', 'Queen Creek', 'Green Valley', 'Oro Valley']
        cities = st.multiselect("Cities", options=all_cities, default=default_cities)

        st.markdown("**Features**")
        col1, col2, col3 = st.columns(3)
        with col1:
            has_yard = st.checkbox("Yard")
        with col2:
            has_pool = st.checkbox("Pool")
        with col3:
            has_solar = st.checkbox("Solar")

        max_age = st.selectbox("Max Age", options=[None, 5, 10, 20, 30], index=4,
                               format_func=lambda x: "Any" if x is None else f"{x} yrs")

        st.divider()

        if st.button("🔄 Refresh Data", use_container_width=True):
            refresh_data()

        if st.button("📥 Export CSV", use_container_width=True):
            if st.session_state.listings:
                df = pd.DataFrame([l.to_dict() for l in st.session_state.listings])
                st.download_button("Download", df.to_csv(index=False),
                                   f"listings_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

    # Load listings
    if not st.session_state.listings:
        load_listings_from_db()

    listings = st.session_state.listings

    # Build filters
    filters = {
        'min_price': min_price, 'max_price': max_price,
        'min_beds': min_beds, 'min_baths': min_baths, 'min_sqft': min_sqft,
        'cities': cities if cities else None,
        'has_yard': has_yard, 'has_pool': has_pool, 'has_solar': has_solar,
        'max_age': max_age
    }

    filtered = filter_listings(listings, filters)

    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Homes", len(filtered))
    with col2:
        avg_score = sum(l.value_score or 0 for l in filtered) / len(filtered) if filtered else 0
        st.metric("Avg Score", f"{avg_score:.0f}")
    with col3:
        prices = [l.price for l in filtered if l.price]
        price_range = f"{format_compact_price(min(prices))}-{format_compact_price(max(prices))}" if prices else "--"
        st.metric("Price Range", price_range)
    with col4:
        sort_by = st.selectbox("Sort", ["Value Score", "Price ↑", "Price ↓", "Largest", "Newest"],
                               label_visibility="collapsed")

    sorted_listings = sort_listings(filtered, sort_by)

    # Empty state
    if not sorted_listings:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #a0a0a0;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🏠</div>
                <h3 style="color: #f0f0f0;">No Listings Found</h3>
                <p>Click the button below to fetch homes from Redfin</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Fetch Listings", use_container_width=True, type="primary"):
                refresh_data()
        return

    # Grid of cards - 4 columns on desktop
    st.markdown("---")
    cols_per_row = 4

    for row_start in range(0, min(len(sorted_listings), 60), cols_per_row):
        cols = st.columns(cols_per_row)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx < len(sorted_listings):
                listing = sorted_listings[idx]
                with col:
                    st.markdown(render_compact_card(listing), unsafe_allow_html=True)
                    with st.expander("Details"):
                        st.write(f"**{listing.address}**")
                        st.write(f"{listing.city}, {listing.state} {listing.zip_code}")
                        st.write(f"**Price:** {format_price(listing.price)}")
                        st.write(f"**HOA:** {'$' + str(listing.hoa_monthly) + '/mo' if listing.hoa_monthly else 'None'}")
                        st.write(f"**Days on Market:** {listing.days_on_market or 'N/A'}")
                        st.write(f"**Crime Index:** {listing.crime_index or 'N/A'}")
                        if listing.url:
                            st.link_button("View on Redfin →", listing.url, use_container_width=True)

    if len(sorted_listings) > 60:
        st.info(f"Showing 60 of {len(sorted_listings)} listings. Adjust filters to narrow results.")


if __name__ == "__main__":
    main()
