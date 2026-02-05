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
from house_hunter.enrichment import enrich_all_listings
from house_hunter.scoring import score_all_listings

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Arizona House Hunter",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-first design
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=DM+Sans:wght@400;500;600&display=swap');

    /* Root variables */
    :root {
        --terracotta: #C4704B;
        --terracotta-dark: #A85A38;
        --sand: #F5F0E8;
        --sand-dark: #E8E0D4;
        --sage: #7A9E7E;
        --night: #2D2A26;
        --cream: #FDFBF7;
        --stone: #6B6560;
    }

    /* Global styles */
    .stApp {
        background-color: var(--sand);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom header */
    .custom-header {
        background: var(--night);
        padding: 1rem 1.5rem;
        margin: -1rem -1rem 1.5rem -1rem;
        border-radius: 0 0 16px 16px;
    }

    .custom-header h1 {
        font-family: 'Fraunces', Georgia, serif;
        color: var(--cream);
        font-size: 1.5rem;
        margin: 0;
    }

    .custom-header p {
        color: var(--stone);
        font-size: 0.85rem;
        margin: 0.25rem 0 0 0;
    }

    /* Stats bar */
    .stats-bar {
        display: flex;
        justify-content: space-around;
        background: var(--cream);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    .stat-item {
        text-align: center;
    }

    .stat-value {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--night);
    }

    .stat-label {
        font-size: 0.7rem;
        color: var(--stone);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Listing card */
    .listing-card {
        background: var(--cream);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .listing-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
    }

    .score-badge {
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        min-width: 56px;
    }

    .score-high { background: #E8F0EA; color: #4A7C59; }
    .score-mid { background: #FDF6E3; color: #B8860B; }
    .score-low { background: #FBF0EC; color: #A0522D; }

    .score-value {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.5rem;
        font-weight: 700;
        line-height: 1;
    }

    .score-label {
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .price-tag {
        text-align: right;
    }

    .price-value {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--night);
    }

    .price-value.ideal { color: #4A7C59; }

    .hoa-tag {
        font-size: 0.75rem;
        color: var(--stone);
    }

    .address {
        font-weight: 500;
        color: var(--night);
        margin-bottom: 0.25rem;
    }

    .location {
        font-size: 0.85rem;
        color: var(--stone);
        margin-bottom: 0.75rem;
    }

    .specs-row {
        display: flex;
        justify-content: space-around;
        padding: 0.75rem 0;
        border-top: 1px solid var(--sand);
        border-bottom: 1px solid var(--sand);
        margin-bottom: 0.75rem;
    }

    .spec-item {
        text-align: center;
    }

    .spec-value {
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 600;
        color: var(--night);
    }

    .spec-label {
        font-size: 0.65rem;
        color: var(--stone);
        text-transform: uppercase;
    }

    .features-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .feature-tag {
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 500;
        background: var(--sand);
        border-radius: 20px;
        color: var(--stone);
    }

    .feature-tag.active {
        background: rgba(122, 158, 126, 0.2);
        color: #5C7D60;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: var(--cream);
    }

    /* Button styling */
    .stButton > button {
        background: var(--terracotta);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        width: 100%;
        transition: background 0.2s;
    }

    .stButton > button:hover {
        background: var(--terracotta-dark);
        color: white;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-family: 'Fraunces', Georgia, serif;
        color: var(--night);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--cream);
        border-radius: 10px;
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
    """Fetch fresh data from Redfin API."""
    with st.spinner("Fetching listings from Redfin..."):
        listings = fetch_listings()

        if not listings:
            st.error("No listings fetched. The API may be temporarily unavailable.")
            return

        st.info(f"Enriching {len(listings)} listings...")
        enriched = enrich_all_listings(listings)

        st.info("Calculating value scores...")
        scored = score_all_listings(enriched)

        # Save to database
        database.delete_all_listings()
        database.save_listings(scored)

        st.session_state.listings = scored
        st.session_state.last_refresh = datetime.now()

        st.success(f"Refreshed {len(scored)} listings!")
        st.rerun()


def get_score_class(score):
    """Get CSS class for score badge."""
    if not score:
        return "score-low"
    if score >= 55:
        return "score-high"
    if score >= 40:
        return "score-mid"
    return "score-low"


def format_price(price):
    """Format price with commas."""
    if not price:
        return "--"
    return f"${price:,.0f}"


def format_number(num):
    """Format number with commas."""
    if not num:
        return "--"
    return f"{num:,.0f}"


def render_listing_card(listing: Listing):
    """Render a single listing card."""
    score_class = get_score_class(listing.value_score)
    price_class = "ideal" if listing.price and listing.price <= 600000 else ""

    features = []
    if listing.has_yard:
        features.append(("Yard", True))
    if listing.has_pool:
        features.append(("Pool", True))
    if listing.has_solar:
        features.append(("Solar", True))
    if listing.year_built:
        features.append((str(listing.year_built), False))

    card_html = f"""
    <div class="listing-card">
        <div class="card-header">
            <div class="score-badge {score_class}">
                <span class="score-value">{listing.value_score or '--'}</span>
                <span class="score-label">Score</span>
            </div>
            <div class="price-tag">
                <div class="price-value {price_class}">{format_price(listing.price)}</div>
                <div class="hoa-tag">{'$' + str(listing.hoa_monthly) + '/mo HOA' if listing.hoa_monthly else 'No HOA'}</div>
            </div>
        </div>
        <div class="address">{listing.address}</div>
        <div class="location">{listing.city}, {listing.state} {listing.zip_code or ''}</div>
        <div class="specs-row">
            <div class="spec-item">
                <div class="spec-value">{listing.beds}</div>
                <div class="spec-label">Beds</div>
            </div>
            <div class="spec-item">
                <div class="spec-value">{listing.baths}</div>
                <div class="spec-label">Baths</div>
            </div>
            <div class="spec-item">
                <div class="spec-value">{format_number(listing.sqft)}</div>
                <div class="spec-label">Sq Ft</div>
            </div>
            <div class="spec-item">
                <div class="spec-value">${int(listing.price / listing.sqft) if listing.price and listing.sqft else '--'}</div>
                <div class="spec-label">Per Ft</div>
            </div>
        </div>
        <div class="features-row">
            {''.join([f'<span class="feature-tag {"active" if active else ""}">{label}</span>' for label, active in features])}
            <span class="feature-tag">{listing.days_on_market or 0} days</span>
            <span class="feature-tag">Crime: {listing.crime_index or '--'}</span>
        </div>
    </div>
    """

    return card_html


def filter_listings(listings, filters):
    """Filter listings based on user selections."""
    filtered = []

    for l in listings:
        # Price
        if filters['min_price'] and l.price and l.price < filters['min_price']:
            continue
        if filters['max_price'] and l.price and l.price > filters['max_price']:
            continue

        # Beds/Baths
        if filters['min_beds'] and l.beds and l.beds < filters['min_beds']:
            continue
        if filters['min_baths'] and l.baths and l.baths < filters['min_baths']:
            continue

        # Sqft
        if filters['min_sqft'] and l.sqft and l.sqft < filters['min_sqft']:
            continue

        # Cities
        if filters['cities'] and l.city not in filters['cities']:
            continue

        # Features
        if filters['has_yard'] and not l.has_yard:
            continue
        if filters['has_pool'] and not l.has_pool:
            continue
        if filters['has_solar'] and not l.has_solar:
            continue

        # Age
        if filters['max_age']:
            current_year = datetime.now().year
            if l.year_built and (current_year - l.year_built) > filters['max_age']:
                continue

        filtered.append(l)

    return filtered


def sort_listings(listings, sort_by, ascending=False):
    """Sort listings by specified field."""
    sort_key = {
        "Value Score": lambda x: x.value_score or 0,
        "Price (Low to High)": lambda x: x.price or 0,
        "Price (High to Low)": lambda x: x.price or 0,
        "Largest": lambda x: x.sqft or 0,
        "Newest": lambda x: x.year_built or 0,
        "Days on Market": lambda x: x.days_on_market or 0,
    }

    reverse = sort_by not in ["Price (Low to High)"]
    return sorted(listings, key=sort_key.get(sort_by, lambda x: x.value_score or 0), reverse=reverse)


def main():
    """Main application."""
    init_session_state()

    # Header
    st.markdown("""
    <div class="custom-header">
        <h1>🏠 Arizona House Hunter</h1>
        <p>Phoenix & Tucson Metro</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")

        # Price range
        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Min Price", value=400000, step=10000, format="%d")
        with col2:
            max_price = st.number_input("Max Price", value=700000, step=10000, format="%d")

        # Beds/Baths
        col1, col2 = st.columns(2)
        with col1:
            min_beds = st.selectbox("Min Beds", options=[1, 2, 3, 4, 5], index=2)
        with col2:
            min_baths = st.selectbox("Min Baths", options=[1, 1.5, 2, 2.5, 3, 3.5, 4], index=2)

        # Sqft
        min_sqft = st.number_input("Min Sq Ft", value=1200, step=100, format="%d")

        # Cities
        all_cities = ['Gilbert', 'Chandler', 'Scottsdale', 'Mesa', 'Queen Creek',
                      'Apache Junction', 'Tucson', 'Green Valley', 'Oro Valley', 'Marana', 'Vail']
        default_cities = ['Gilbert', 'Chandler', 'Scottsdale', 'Queen Creek', 'Green Valley', 'Oro Valley']
        cities = st.multiselect("Cities", options=all_cities, default=default_cities)

        # Features
        st.markdown("**Features**")
        col1, col2, col3 = st.columns(3)
        with col1:
            has_yard = st.checkbox("Yard")
        with col2:
            has_pool = st.checkbox("Pool")
        with col3:
            has_solar = st.checkbox("Solar")

        # Max age
        max_age = st.selectbox("Max Age", options=[None, 5, 10, 20, 30], index=4,
                               format_func=lambda x: "Any" if x is None else f"{x} years")

        st.divider()

        # Actions
        if st.button("🔄 Refresh Data", use_container_width=True):
            refresh_data()

        if st.button("📥 Export CSV", use_container_width=True):
            listings = st.session_state.listings
            if listings:
                df = pd.DataFrame([l.to_dict() for l in listings])
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download",
                    data=csv,
                    file_name=f"listings_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

    # Load listings
    if not st.session_state.listings:
        load_listings_from_db()

    listings = st.session_state.listings

    # Build filters dict
    filters = {
        'min_price': min_price,
        'max_price': max_price,
        'min_beds': min_beds,
        'min_baths': min_baths,
        'min_sqft': min_sqft,
        'cities': cities if cities else None,
        'has_yard': has_yard,
        'has_pool': has_pool,
        'has_solar': has_solar,
        'max_age': max_age
    }

    # Filter listings
    filtered = filter_listings(listings, filters)

    # Stats bar
    if filtered:
        avg_score = sum(l.value_score or 0 for l in filtered) / len(filtered)
        prices = [l.price for l in filtered if l.price]
        min_p = min(prices) if prices else 0
        max_p = max(prices) if prices else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Homes", len(filtered))
        with col2:
            st.metric("Avg Score", f"{avg_score:.0f}")
        with col3:
            st.metric("Price Range", f"${min_p/1000:.0f}K-${max_p/1000:.0f}K")

    # Sort control
    col1, col2 = st.columns([2, 1])
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            options=["Value Score", "Price (Low to High)", "Price (High to Low)",
                     "Largest", "Newest", "Days on Market"],
            label_visibility="collapsed"
        )

    # Sort and display listings
    sorted_listings = sort_listings(filtered, sort_by)

    if not sorted_listings:
        st.info("No listings found. Try adjusting your filters or click 'Refresh Data' to fetch new listings.")
    else:
        # Display listings as cards
        for listing in sorted_listings[:50]:  # Limit to 50 for performance
            card_html = render_listing_card(listing)
            st.markdown(card_html, unsafe_allow_html=True)

            # Expandable details
            with st.expander(f"View Details: {listing.address}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Property Details**")
                    st.write(f"- Lot Size: {format_number(listing.lot_sqft)} sqft" if listing.lot_sqft else "- Lot Size: N/A")
                    st.write(f"- Stories: {listing.stories or 'N/A'}")
                    st.write(f"- HOA: {'$' + str(listing.hoa_monthly) + '/mo' if listing.hoa_monthly else 'None'}")
                    st.write(f"- Days on Market: {listing.days_on_market or 'N/A'}")

                with col2:
                    st.markdown("**Features**")
                    st.write(f"- Yard: {'Yes' if listing.has_yard else 'No'}")
                    st.write(f"- Pool: {'Yes' if listing.has_pool else 'No'}")
                    st.write(f"- Solar: {'Yes' if listing.has_solar else 'No'}")
                    st.write(f"- Crime Index: {listing.crime_index or 'N/A'}")

                st.markdown("**Score Breakdown**")
                breakdown_data = {
                    "Factor": ["Location (25%)", "Sq Ft per Dollar (23%)", "Year Built (20%)",
                               "Low HOA (13%)", "Private Yard (10%)", "Days on Market (3%)",
                               "Pool (3%)", "Solar (3%)"],
                    "Value": [
                        listing.city or "N/A",
                        f"{(listing.sqft / listing.price * 1000):.1f} sqft/$1k" if listing.sqft and listing.price else "N/A",
                        str(listing.year_built) if listing.year_built else "N/A",
                        f"${listing.hoa_monthly}/mo" if listing.hoa_monthly else "None",
                        "Yes" if listing.has_yard else "No",
                        f"{listing.days_on_market} days" if listing.days_on_market is not None else "N/A",
                        "Yes" if listing.has_pool else "No",
                        "Yes" if listing.has_solar else "No"
                    ]
                }
                st.dataframe(pd.DataFrame(breakdown_data), hide_index=True, use_container_width=True)

                if listing.url:
                    st.link_button("View on Redfin →", listing.url, use_container_width=True)

        if len(sorted_listings) > 50:
            st.info(f"Showing 50 of {len(sorted_listings)} listings. Adjust filters to narrow results.")


if __name__ == "__main__":
    main()
