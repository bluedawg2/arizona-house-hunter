# Arizona House Hunter 🏠

A mobile-friendly real estate listing analysis tool for the Phoenix & Tucson metro areas. Fetches listings from Redfin, applies smart filters, and calculates value scores to help you find the best deals.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Smart Filtering** - Beds, baths, sqft, price range, property age, and city selection
- **Value Scoring** - Weighted algorithm considering price per sqft, location, HOA, amenities, and more
- **Data Enrichment** - Crime indices, distance to downtown, yard detection
- **Mobile-First Design** - Touch-friendly cards, collapsible filters, responsive layout
- **Two UI Options** - Flask web app or Streamlit app

## Quick Start

### Installation

```bash
git clone https://github.com/bluedawg2/arizona-house-hunter.git
cd arizona-house-hunter
pip install -r requirements.txt
```

### Run Flask App

```bash
python -m house_hunter
```

Open http://localhost:5000 in your browser.

### Run Streamlit App

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501 in your browser.

## Value Score Algorithm

Properties are scored 0-100 based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| Location | 25% | City preference (Scottsdale, Gilbert rated highest) |
| Sq Ft per Dollar | 23% | More space for your money = higher score |
| Year Built | 20% | Newer properties score better |
| Low HOA | 13% | Lower monthly HOA = higher score |
| Private Yard | 10% | Properties with yards get bonus points |
| Days on Market | 3% | Longer listings may indicate negotiation room |
| Pool | 3% | Bonus for pool |
| Solar | 3% | Bonus for solar panels |

## Hard Filters

Listings must meet these criteria to appear:

- Minimum 3 bedrooms, 2 bathrooms
- At least 1,200 square feet
- Price: $400,000 - $700,000
- Built 1996 or later (30 years max)
- Single-family or townhouse only (no condos/apartments)

## Project Structure

```
arizona-house-hunter/
├── streamlit_app.py      # Streamlit web application
├── requirements.txt      # Python dependencies
├── house_hunter/
│   ├── __main__.py       # Flask entry point
│   ├── app.py            # Flask application
│   ├── api.py            # REST API endpoints
│   ├── config.py         # Configuration settings
│   ├── database.py       # SQLite operations
│   ├── fetcher.py        # Redfin API scraper
│   ├── enrichment.py     # Data enrichment (geocoding, crime)
│   ├── scoring.py        # Value score calculation
│   ├── models.py         # Data models
│   ├── static/           # Frontend assets
│   └── tests/            # Unit tests
└── TESTING_PLAN.md       # Comprehensive testing checklist
```

## API Endpoints (Flask)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/listings` | GET | Get filtered listings |
| `/api/listings/<id>` | GET | Get single listing with score breakdown |
| `/api/refresh` | POST | Fetch fresh data from Redfin |
| `/api/stats` | GET | Get summary statistics |
| `/api/export` | GET | Download CSV export |

## Running Tests

```bash
python -m unittest discover -s house_hunter/tests -v
```

## Deployment to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository
5. Set main file: `streamlit_app.py`
6. Deploy!

## Tech Stack

- **Backend**: Python, Flask, SQLite
- **Frontend**: HTML/CSS/JS (Flask) or Streamlit
- **Data Sources**: Redfin Stingray API, OpenStreetMap Nominatim
- **Design**: Desert Modernism aesthetic with terracotta/sand/sage palette

## License

MIT License - feel free to use and modify for your own house hunting!

---

Built with 🌵 for Arizona home buyers
