/**
 * Arizona House Hunter - Modern Mobile-First UI
 * Desert Modernism Edition
 */

// ============================================
// State Management
// ============================================
const state = {
    listings: [],
    displayedCount: 0,
    pageSize: 20,
    isLoading: false,
    filters: {
        minPrice: 400000,
        maxPrice: 700000,
        minBeds: 3,
        minBaths: 2,
        minSqft: 1200,
        cities: ['Gilbert', 'Chandler', 'Scottsdale', 'Queen Creek', 'Green Valley', 'Oro Valley'],
        hasYard: false,
        hasPool: false,
        hasSolar: false,
        maxAge: 30
    },
    sort: {
        field: 'value_score',
        dir: 'desc'
    }
};

// ============================================
// DOM Elements
// ============================================
const dom = {
    // Filter panel
    filterPanel: null,
    filterOverlay: null,
    filterToggle: null,
    closeFilters: null,
    filterBadge: null,
    applyFilters: null,
    resetFilters: null,

    // Filter inputs
    minPrice: null,
    maxPrice: null,
    minBeds: null,
    minBaths: null,
    minSqft: null,
    cityChips: null,
    hasYard: null,
    hasPool: null,
    hasSolar: null,
    maxAge: null,
    ageButtons: null,

    // Listings
    listingsGrid: null,
    loadingEl: null,
    errorEl: null,
    emptyEl: null,
    loadMoreContainer: null,
    loadMoreBtn: null,

    // Stats
    listingCount: null,
    avgScore: null,
    priceRange: null,

    // Actions
    sortSelect: null,
    refreshBtn: null,
    exportBtn: null,

    // Modal
    modal: null,
    modalBody: null,

    // Toast
    toastContainer: null
};

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initDom();
    initEventListeners();
    loadListings();
});

function initDom() {
    // Filter panel
    dom.filterPanel = document.getElementById('filter-panel');
    dom.filterOverlay = document.getElementById('filter-overlay');
    dom.filterToggle = document.getElementById('filter-toggle');
    dom.closeFilters = document.getElementById('close-filters');
    dom.filterBadge = document.getElementById('filter-badge');
    dom.applyFilters = document.getElementById('apply-filters');
    dom.resetFilters = document.getElementById('reset-filters');

    // Filter inputs
    dom.minPrice = document.getElementById('min-price');
    dom.maxPrice = document.getElementById('max-price');
    dom.minBeds = document.getElementById('min-beds');
    dom.minBaths = document.getElementById('min-baths');
    dom.minSqft = document.getElementById('min-sqft');
    dom.cityChips = document.getElementById('city-filters');
    dom.hasYard = document.getElementById('has-yard');
    dom.hasPool = document.getElementById('has-pool');
    dom.hasSolar = document.getElementById('has-solar');
    dom.maxAge = document.getElementById('max-age');
    dom.ageButtons = document.querySelectorAll('.age-btn');

    // Listings
    dom.listingsGrid = document.getElementById('listings-grid');
    dom.loadingEl = document.getElementById('loading');
    dom.errorEl = document.getElementById('error');
    dom.emptyEl = document.getElementById('empty');
    dom.loadMoreContainer = document.getElementById('load-more-container');
    dom.loadMoreBtn = document.getElementById('load-more');

    // Stats
    dom.listingCount = document.getElementById('listing-count');
    dom.avgScore = document.getElementById('avg-score');
    dom.priceRange = document.getElementById('price-range');

    // Actions
    dom.sortSelect = document.getElementById('sort-select');
    dom.refreshBtn = document.getElementById('refresh-btn');
    dom.exportBtn = document.getElementById('export-btn');

    // Modal
    dom.modal = document.getElementById('detail-modal');
    dom.modalBody = document.getElementById('modal-body');

    // Toast
    dom.toastContainer = document.getElementById('toast-container');
}

function initEventListeners() {
    // Filter panel toggle (mobile)
    dom.filterToggle.addEventListener('click', openFilters);
    dom.closeFilters.addEventListener('click', closeFilters);
    dom.filterOverlay.addEventListener('click', closeFilters);

    // Filter actions
    dom.applyFilters.addEventListener('click', () => {
        applyFilters();
        closeFilters();
    });
    dom.resetFilters.addEventListener('click', resetFilters);

    // Stepper buttons
    document.querySelectorAll('.stepper-btn').forEach(btn => {
        btn.addEventListener('click', handleStepper);
    });

    // City chips
    dom.cityChips.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            chip.classList.toggle('active');
        });
    });

    // Age buttons
    dom.ageButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            dom.ageButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            dom.maxAge.value = btn.dataset.age;
        });
    });

    // Sort
    dom.sortSelect.addEventListener('change', handleSort);

    // Actions
    dom.refreshBtn.addEventListener('click', refreshData);
    dom.exportBtn.addEventListener('click', exportCSV);
    document.getElementById('refresh-empty')?.addEventListener('click', refreshData);

    // Load more
    dom.loadMoreBtn?.addEventListener('click', loadMore);

    // Modal
    dom.modal.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-backdrop') ||
            e.target.closest('.modal-close')) {
            closeModal();
        }
    });

    // Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (dom.modal.classList.contains('open')) {
                closeModal();
            } else if (dom.filterPanel.classList.contains('open')) {
                closeFilters();
            }
        }
    });

    // Prevent body scroll when filter/modal open
    dom.filterPanel.addEventListener('touchmove', (e) => e.stopPropagation());
    dom.modal.addEventListener('touchmove', (e) => e.stopPropagation());
}

// ============================================
// Filter Panel
// ============================================
function openFilters() {
    dom.filterPanel.classList.add('open');
    dom.filterOverlay.classList.add('visible');
    document.body.classList.add('no-scroll');
}

function closeFilters() {
    dom.filterPanel.classList.remove('open');
    dom.filterOverlay.classList.remove('visible');
    document.body.classList.remove('no-scroll');
}

function handleStepper(e) {
    const btn = e.currentTarget;
    const action = btn.dataset.action;
    const targetId = btn.dataset.target;
    const input = document.getElementById(targetId);

    let value = parseFloat(input.value) || 0;
    const step = parseFloat(input.step) || 1;
    const min = parseFloat(input.min) || 0;
    const max = parseFloat(input.max) || 999;

    if (action === 'increment' && value < max) {
        value += step;
    } else if (action === 'decrement' && value > min) {
        value -= step;
    }

    input.value = value;
}

function applyFilters() {
    // Read filter values
    state.filters.minPrice = parseInt(dom.minPrice.value) || 0;
    state.filters.maxPrice = parseInt(dom.maxPrice.value) || 999999999;
    state.filters.minBeds = parseInt(dom.minBeds.value) || 0;
    state.filters.minBaths = parseFloat(dom.minBaths.value) || 0;
    state.filters.minSqft = parseInt(dom.minSqft.value) || 0;

    // Cities
    const activeCities = [];
    dom.cityChips.querySelectorAll('.chip.active').forEach(chip => {
        activeCities.push(chip.dataset.city);
    });
    state.filters.cities = activeCities;

    // Features
    state.filters.hasYard = dom.hasYard.checked;
    state.filters.hasPool = dom.hasPool.checked;
    state.filters.hasSolar = dom.hasSolar.checked;

    // Age
    state.filters.maxAge = dom.maxAge.value ? parseInt(dom.maxAge.value) : null;

    // Update badge
    updateFilterBadge();

    // Reload
    loadListings();
}

function resetFilters() {
    // Reset values
    dom.minPrice.value = 400000;
    dom.maxPrice.value = 700000;
    dom.minBeds.value = 3;
    dom.minBaths.value = 2;
    dom.minSqft.value = 1200;

    // Reset cities
    const defaultCities = ['Gilbert', 'Chandler', 'Scottsdale', 'Queen Creek', 'Green Valley', 'Oro Valley'];
    dom.cityChips.querySelectorAll('.chip').forEach(chip => {
        chip.classList.toggle('active', defaultCities.includes(chip.dataset.city));
    });

    // Reset features
    dom.hasYard.checked = false;
    dom.hasPool.checked = false;
    dom.hasSolar.checked = false;

    // Reset age
    dom.ageButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.age === '30');
    });
    dom.maxAge.value = 30;

    // Reset state
    state.filters = {
        minPrice: 400000,
        maxPrice: 700000,
        minBeds: 3,
        minBaths: 2,
        minSqft: 1200,
        cities: defaultCities,
        hasYard: false,
        hasPool: false,
        hasSolar: false,
        maxAge: 30
    };

    updateFilterBadge();
    loadListings();
}

function updateFilterBadge() {
    // Count active filters (beyond defaults)
    let count = 0;
    if (state.filters.minPrice !== 400000) count++;
    if (state.filters.maxPrice !== 700000) count++;
    if (state.filters.minBeds !== 3) count++;
    if (state.filters.minBaths !== 2) count++;
    if (state.filters.minSqft !== 1200) count++;
    if (state.filters.hasYard) count++;
    if (state.filters.hasPool) count++;
    if (state.filters.hasSolar) count++;
    if (state.filters.maxAge !== 30 && state.filters.maxAge !== null) count++;

    if (count > 0) {
        dom.filterBadge.textContent = count;
        dom.filterBadge.classList.add('visible');
    } else {
        dom.filterBadge.classList.remove('visible');
    }
}

// ============================================
// Data Loading
// ============================================
async function loadListings() {
    if (state.isLoading) return;
    state.isLoading = true;

    showLoading(true);
    hideError();
    hideEmpty();

    try {
        const params = buildQueryParams();
        const response = await fetch(`/api/listings?${params}`);
        const data = await response.json();

        if (data.success) {
            state.listings = data.listings;
            state.displayedCount = 0;

            updateStats(data.listings);
            renderListings();

            if (data.listings.length === 0) {
                showEmpty();
            }
        } else {
            showError(data.error || 'Failed to load listings');
        }
    } catch (err) {
        console.error('Error loading listings:', err);
        showError('Failed to connect to server. Is the backend running?');
    } finally {
        state.isLoading = false;
        showLoading(false);
    }
}

function buildQueryParams() {
    const params = new URLSearchParams();

    if (state.filters.minPrice) params.append('min_price', state.filters.minPrice);
    if (state.filters.maxPrice) params.append('max_price', state.filters.maxPrice);
    if (state.filters.minBeds) params.append('min_beds', state.filters.minBeds);
    if (state.filters.minBaths) params.append('min_baths', state.filters.minBaths);
    if (state.filters.minSqft) params.append('min_sqft', state.filters.minSqft);

    if (state.filters.cities.length > 0 && state.filters.cities.length < 11) {
        params.append('cities', state.filters.cities.join(','));
    }

    if (state.filters.hasYard) params.append('has_yard', 'true');
    if (state.filters.hasPool) params.append('has_pool', 'true');
    if (state.filters.hasSolar) params.append('has_solar', 'true');
    if (state.filters.maxAge) params.append('max_age', state.filters.maxAge);

    params.append('sort_by', state.sort.field);
    params.append('sort_dir', state.sort.dir);

    return params.toString();
}

function updateStats(listings) {
    // Count
    dom.listingCount.textContent = listings.length;

    // Average score
    if (listings.length > 0) {
        const avgScore = listings.reduce((sum, l) => sum + (l.value_score || 0), 0) / listings.length;
        dom.avgScore.textContent = Math.round(avgScore);

        // Price range
        const prices = listings.map(l => l.price).filter(p => p);
        if (prices.length > 0) {
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            dom.priceRange.textContent = `$${formatCompact(minPrice)}-${formatCompact(maxPrice)}`;
        }
    } else {
        dom.avgScore.textContent = '--';
        dom.priceRange.textContent = '--';
    }
}

// ============================================
// Rendering
// ============================================
function renderListings() {
    const toShow = state.listings.slice(0, state.displayedCount + state.pageSize);
    state.displayedCount = toShow.length;

    dom.listingsGrid.innerHTML = toShow.map(listing => createListingCard(listing)).join('');

    // Attach click handlers
    dom.listingsGrid.querySelectorAll('.listing-card').forEach((card, index) => {
        card.addEventListener('click', () => showDetail(toShow[index]));
    });

    // Show/hide load more
    if (state.displayedCount < state.listings.length) {
        dom.loadMoreContainer.classList.remove('hidden');
    } else {
        dom.loadMoreContainer.classList.add('hidden');
    }

    // Animate cards in
    requestAnimationFrame(() => {
        dom.listingsGrid.querySelectorAll('.listing-card').forEach((card, i) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            setTimeout(() => {
                card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, i * 50);
        });
    });
}

function createListingCard(listing) {
    const scoreClass = getScoreClass(listing.value_score);
    const priceClass = listing.price <= 600000 ? 'ideal' : '';
    const crimeClass = getCrimeClass(listing.crime_index);

    const features = [];
    if (listing.has_yard) features.push({ icon: 'yard', label: 'Yard', highlight: true });
    if (listing.has_pool) features.push({ icon: 'pool', label: 'Pool', highlight: true });
    if (listing.has_solar) features.push({ icon: 'solar', label: 'Solar', highlight: true });
    if (listing.year_built) features.push({ icon: 'year', label: listing.year_built });
    if (listing.stories) features.push({ icon: 'stories', label: `${listing.stories} Story` });

    return `
        <article class="listing-card" data-id="${listing.id}">
            <div class="card-header">
                <div class="card-score ${scoreClass}">
                    <span class="score-value">${listing.value_score || '--'}</span>
                    <span class="score-label">Score</span>
                </div>
                <div class="card-price">
                    <div class="price ${priceClass}">$${formatNumber(listing.price)}</div>
                    ${listing.hoa_monthly ? `<div class="hoa">$${listing.hoa_monthly}/mo HOA</div>` : '<div class="hoa">No HOA</div>'}
                </div>
            </div>
            <div class="card-body">
                <div class="card-address">${listing.address}</div>
                <div class="card-location">${listing.city}, ${listing.state} ${listing.zip_code || ''}</div>
                <div class="card-specs">
                    <div class="spec-item">
                        <span class="spec-value">${listing.beds}</span>
                        <span class="spec-label">Beds</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-value">${listing.baths}</span>
                        <span class="spec-label">Baths</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-value">${formatNumber(listing.sqft)}</span>
                        <span class="spec-label">Sq Ft</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-value">$${Math.round(listing.price / listing.sqft)}</span>
                        <span class="spec-label">Per Ft</span>
                    </div>
                </div>
                <div class="card-features">
                    ${features.map(f => `
                        <span class="feature-tag ${f.highlight ? 'highlight' : ''}">
                            ${getFeatureIcon(f.icon)}
                            ${f.label}
                        </span>
                    `).join('')}
                </div>
            </div>
            <div class="card-footer">
                <div class="card-meta">
                    <span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                        ${listing.days_on_market || 0} days
                    </span>
                    <span class="crime-badge ${crimeClass}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        ${listing.crime_index || '--'}
                    </span>
                </div>
            </div>
        </article>
    `;
}

function getFeatureIcon(type) {
    const icons = {
        yard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>',
        pool: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="12" rx="10" ry="5"/></svg>',
        solar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
        year: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
        stories: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M3 10h18M3 7l9-4 9 4M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/></svg>'
    };
    return icons[type] || '';
}

function getScoreClass(score) {
    if (!score) return 'score-low';
    if (score >= 55) return 'score-high';
    if (score >= 40) return 'score-mid';
    return 'score-low';
}

function getCrimeClass(index) {
    if (!index) return '';
    if (index >= 70) return 'safe';
    if (index >= 50) return 'moderate';
    return 'concern';
}

function loadMore() {
    renderListings();
}

// ============================================
// Detail Modal
// ============================================
function showDetail(listing) {
    const scoreClass = getScoreClass(listing.value_score);

    dom.modalBody.innerHTML = `
        <div class="modal-handle"></div>
        <button class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
        </button>

        <div class="detail-header">
            <div class="detail-score ${scoreClass}">
                <span class="score-value">${listing.value_score || '--'}</span>
                <span class="score-label">Value Score</span>
            </div>
            <div class="detail-price">$${formatNumber(listing.price)}</div>
            <div class="detail-address">${listing.address}</div>
            <div class="detail-location">${listing.city}, ${listing.state} ${listing.zip_code || ''}</div>
        </div>

        <div class="detail-specs">
            <div class="detail-spec">
                <span class="value">${listing.beds}</span>
                <span class="label">Beds</span>
            </div>
            <div class="detail-spec">
                <span class="value">${listing.baths}</span>
                <span class="label">Baths</span>
            </div>
            <div class="detail-spec">
                <span class="value">${formatNumber(listing.sqft)}</span>
                <span class="label">Sq Ft</span>
            </div>
            <div class="detail-spec">
                <span class="value">${listing.year_built || '--'}</span>
                <span class="label">Year</span>
            </div>
        </div>

        <div class="detail-section">
            <h3>Property Details</h3>
            <div class="detail-features">
                <div class="detail-feature">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    ${listing.lot_sqft ? formatNumber(listing.lot_sqft) + ' sqft lot' : 'Lot size N/A'}
                </div>
                <div class="detail-feature">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
                    ${listing.stories || '1'} ${listing.stories === 1 ? 'Story' : 'Stories'}
                </div>
                <div class="detail-feature">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
                    ${listing.hoa_monthly ? '$' + listing.hoa_monthly + '/mo HOA' : 'No HOA'}
                </div>
                <div class="detail-feature">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                    ${listing.days_on_market || 0} days on market
                </div>
                <div class="detail-feature ${listing.has_yard ? 'active' : ''}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
                    ${listing.has_yard ? 'Has Yard' : 'No Yard'}
                </div>
                <div class="detail-feature ${listing.has_pool ? 'active' : ''}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="12" rx="10" ry="5"/></svg>
                    ${listing.has_pool ? 'Has Pool' : 'No Pool'}
                </div>
                <div class="detail-feature ${listing.has_solar ? 'active' : ''}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2"/></svg>
                    ${listing.has_solar ? 'Has Solar' : 'No Solar'}
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3>Location & Safety</h3>
            <div class="detail-features">
                <div class="detail-feature ${getCrimeClass(listing.crime_index) === 'safe' ? 'active' : ''}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    Crime Index: ${listing.crime_index || 'N/A'}
                </div>
                ${listing.distance_to_downtown ? `
                <div class="detail-feature">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 000 20 14.5 14.5 0 000-20M2 12h20"/></svg>
                    ${listing.distance_to_downtown} mi to ${listing.nearest_downtown || 'downtown'}
                </div>
                ` : ''}
            </div>
        </div>

        <div class="detail-section">
            <h3>Score Breakdown</h3>
            <div class="score-breakdown">
                ${createBreakdownRow('Location (25%)', listing.city)}
                ${createBreakdownRow('Sq Ft per Dollar (23%)', listing.sqft && listing.price ? (listing.sqft / listing.price * 1000).toFixed(1) + ' sqft/$1k' : '--')}
                ${createBreakdownRow('Year Built (20%)', listing.year_built || '--')}
                ${createBreakdownRow('Low HOA (13%)', listing.hoa_monthly ? '$' + listing.hoa_monthly : 'None')}
                ${createBreakdownRow('Private Yard (10%)', listing.has_yard ? 'Yes' : 'No')}
                ${createBreakdownRow('Days on Market (3%)', listing.days_on_market !== null ? listing.days_on_market + ' days' : '--')}
                ${createBreakdownRow('Pool (3%)', listing.has_pool ? 'Yes' : 'No')}
                ${createBreakdownRow('Solar (3%)', listing.has_solar ? 'Yes' : 'No')}
            </div>
        </div>

        <div class="detail-actions">
            ${listing.url ? `
                <a href="${listing.url}" target="_blank" rel="noopener" class="btn-redfin">
                    View on Redfin
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"/>
                    </svg>
                </a>
            ` : ''}
        </div>
    `;

    dom.modal.classList.remove('hidden');
    requestAnimationFrame(() => {
        dom.modal.classList.add('open');
    });
    document.body.classList.add('no-scroll');
}

function createBreakdownRow(label, value) {
    return `
        <div class="breakdown-row">
            <span class="breakdown-label">${label}</span>
            <span class="breakdown-value">${value}</span>
        </div>
    `;
}

function closeModal() {
    dom.modal.classList.remove('open');
    document.body.classList.remove('no-scroll');
    setTimeout(() => {
        dom.modal.classList.add('hidden');
    }, 300);
}

// ============================================
// Actions
// ============================================
function handleSort() {
    const [field, dir] = dom.sortSelect.value.split('-');
    state.sort.field = field;
    state.sort.dir = dir;
    loadListings();
}

async function refreshData() {
    dom.refreshBtn.disabled = true;
    dom.refreshBtn.classList.add('loading');
    dom.refreshBtn.querySelector('span').textContent = 'Refreshing...';

    showLoading(true);
    hideError();
    hideEmpty();

    try {
        const response = await fetch('/api/refresh', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showToast(`Refreshed ${data.count} listings`, 'success');
            await loadListings();
        } else {
            showError(data.error || 'Failed to refresh data');
            showToast('Refresh failed', 'error');
        }
    } catch (err) {
        console.error('Error refreshing:', err);
        showError('Failed to refresh data. Check console for details.');
        showToast('Connection error', 'error');
    } finally {
        dom.refreshBtn.disabled = false;
        dom.refreshBtn.classList.remove('loading');
        dom.refreshBtn.querySelector('span').textContent = 'Refresh';
        showLoading(false);
    }
}

function exportCSV() {
    window.location.href = '/api/export';
    showToast('Downloading CSV...', 'success');
}

// ============================================
// UI States
// ============================================
function showLoading(show) {
    dom.loadingEl.classList.toggle('hidden', !show);
    if (show) {
        dom.listingsGrid.innerHTML = '';
        dom.loadMoreContainer.classList.add('hidden');
    }
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    dom.errorEl.classList.remove('hidden');
}

function hideError() {
    dom.errorEl.classList.add('hidden');
}

function showEmpty() {
    dom.emptyEl.classList.remove('hidden');
}

function hideEmpty() {
    dom.emptyEl.classList.add('hidden');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    dom.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// Utilities
// ============================================
function formatNumber(num) {
    if (num === null || num === undefined) return '--';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatCompact(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return Math.round(num / 1000) + 'K';
    }
    return num.toString();
}
