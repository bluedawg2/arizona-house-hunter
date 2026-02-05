/**
 * Arizona House Hunter - Frontend Application
 */

// Global state
let dataTable = null;
let allListings = [];

// DOM Elements
const elements = {
    table: null,
    refreshBtn: null,
    exportBtn: null,
    applyFiltersBtn: null,
    resetFiltersBtn: null,
    loadingEl: null,
    errorEl: null,
    listingCount: null,
    modal: null,
    modalBody: null,
};

// Initialize on DOM ready
$(document).ready(function() {
    initializeElements();
    initializeDataTable();
    loadListings();
    bindEvents();
});

function initializeElements() {
    elements.table = $('#listings-table');
    elements.refreshBtn = $('#refresh-btn');
    elements.exportBtn = $('#export-btn');
    elements.applyFiltersBtn = $('#apply-filters');
    elements.resetFiltersBtn = $('#reset-filters');
    elements.loadingEl = $('#loading');
    elements.errorEl = $('#error');
    elements.listingCount = $('#listing-count');
    elements.modal = $('#detail-modal');
    elements.modalBody = $('#modal-body');
}

function initializeDataTable() {
    dataTable = elements.table.DataTable({
        data: [],
        columns: [
            {
                data: 'value_score',
                render: function(data) {
                    if (data === null) return '-';
                    let scoreClass = 'score-low';
                    if (data >= 60) scoreClass = 'score-high';
                    else if (data >= 40) scoreClass = 'score-medium';
                    return `<span class="value-score ${scoreClass}">${data}</span>`;
                }
            },
            { data: 'address' },
            { data: 'city' },
            {
                data: 'price',
                render: function(data) {
                    const priceClass = data <= 600000 ? 'price-ideal' : '';
                    return `<span class="price ${priceClass}">$${formatNumber(data)}</span>`;
                }
            },
            { data: 'beds' },
            { data: 'baths' },
            { data: 'sqft', render: formatNumber },
            { data: 'year_built', render: (d) => d || '-' },
            { data: 'stories', render: (d) => d || '-' },
            {
                data: 'hoa_monthly',
                render: (d) => d ? `$${d}` : '-'
            },
            {
                data: 'days_on_market',
                render: (d) => d !== null ? d : '-'
            },
            {
                data: 'has_yard',
                render: (d) => d ? '<span class="feature-yes">✓</span>' : '<span class="feature-no">-</span>'
            },
            {
                data: 'has_pool',
                render: (d) => d ? '<span class="feature-yes">✓</span>' : '<span class="feature-no">-</span>'
            },
            {
                data: 'crime_index',
                render: function(d) {
                    if (!d) return '-';
                    let cls = 'crime-low';
                    if (d >= 70) cls = 'crime-safe';
                    else if (d >= 50) cls = 'crime-moderate';
                    return `<span class="${cls}">${d}</span>`;
                }
            }
        ],
        order: [[0, 'desc']], // Sort by value score descending
        pageLength: 25,
        lengthMenu: [10, 25, 50, 100],
        responsive: true,
        language: {
            emptyTable: 'No listings found. Click "Refresh Data" to fetch listings.',
            zeroRecords: 'No listings match your filters.'
        }
    });

    // Row click handler
    elements.table.on('click', 'tbody tr', function() {
        const data = dataTable.row(this).data();
        if (data) {
            showListingDetail(data);
        }
    });
}

function bindEvents() {
    // Refresh button
    elements.refreshBtn.on('click', refreshData);

    // Export button
    elements.exportBtn.on('click', exportCSV);

    // Apply filters
    elements.applyFiltersBtn.on('click', applyFilters);

    // Reset filters
    elements.resetFiltersBtn.on('click', resetFilters);

    // Modal close
    $('.close-modal').on('click', closeModal);
    elements.modal.on('click', function(e) {
        if (e.target === this) closeModal();
    });

    // Escape key closes modal
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') closeModal();
    });

    // Enter key in filter inputs applies filters
    $('.filters input').on('keypress', function(e) {
        if (e.key === 'Enter') applyFilters();
    });
}

async function loadListings() {
    showLoading(true);
    hideError();

    try {
        const params = getFilterParams();
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`/api/listings?${queryString}`);
        const data = await response.json();

        if (data.success) {
            allListings = data.listings;
            updateTable(data.listings);
            updateListingCount(data.count);
        } else {
            showError(data.error || 'Failed to load listings');
        }
    } catch (err) {
        console.error('Error loading listings:', err);
        showError('Failed to connect to server. Is the backend running?');
    } finally {
        showLoading(false);
    }
}

async function refreshData() {
    elements.refreshBtn.prop('disabled', true);
    elements.refreshBtn.html('<span class="refresh-icon">↻</span> Refreshing...');
    showLoading(true);
    hideError();

    try {
        const response = await fetch('/api/refresh', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            await loadListings();
            alert(`Successfully refreshed ${data.count} listings!`);
        } else {
            showError(data.error || 'Failed to refresh data');
        }
    } catch (err) {
        console.error('Error refreshing data:', err);
        showError('Failed to refresh data. Check console for details.');
    } finally {
        elements.refreshBtn.prop('disabled', false);
        elements.refreshBtn.html('<span class="refresh-icon">↻</span> Refresh Data');
        showLoading(false);
    }
}

function applyFilters() {
    loadListings();
}

function resetFilters() {
    // Reset to defaults
    $('#min-price').val(400000);
    $('#max-price').val(700000);
    $('#min-beds').val('3');
    $('#min-baths').val('2');
    $('#min-sqft').val(1200);
    $('#max-age').val('30');

    // Set default cities (exclude Mesa, Apache Junction, Tucson, Marana, Vail)
    $('#city-filters input[type="checkbox"]').prop('checked', false);
    const defaultCities = ['Gilbert', 'Chandler', 'Scottsdale', 'Queen Creek', 'Green Valley', 'Oro Valley'];
    defaultCities.forEach(city => {
        $(`#city-filters input[value="${city}"]`).prop('checked', true);
    });

    // Uncheck features
    $('#has-yard').prop('checked', false);
    $('#has-pool').prop('checked', false);
    $('#has-solar').prop('checked', false);

    loadListings();
}

function getFilterParams() {
    const params = {};

    const minPrice = $('#min-price').val();
    const maxPrice = $('#max-price').val();
    const minBeds = $('#min-beds').val();
    const minBaths = $('#min-baths').val();
    const minSqft = $('#min-sqft').val();
    const maxAge = $('#max-age').val();

    if (minPrice) params.min_price = minPrice;
    if (maxPrice) params.max_price = maxPrice;
    if (minBeds) params.min_beds = minBeds;
    if (minBaths) params.min_baths = minBaths;
    if (minSqft) params.min_sqft = minSqft;
    if (maxAge) params.max_age = maxAge;

    // Cities
    const selectedCities = [];
    $('#city-filters input:checked').each(function() {
        selectedCities.push($(this).val());
    });
    if (selectedCities.length > 0 && selectedCities.length < 11) {
        params.cities = selectedCities.join(',');
    }

    // Features
    if ($('#has-yard').is(':checked')) params.has_yard = 'true';
    if ($('#has-pool').is(':checked')) params.has_pool = 'true';
    if ($('#has-solar').is(':checked')) params.has_solar = 'true';

    return params;
}

function updateTable(listings) {
    dataTable.clear();
    dataTable.rows.add(listings);
    dataTable.draw();
}

function updateListingCount(count) {
    elements.listingCount.text(`${count} listing${count !== 1 ? 's' : ''}`);
}

function showListingDetail(listing) {
    const html = `
        <div class="listing-detail">
            <h2>${listing.address}</h2>
            <p>${listing.city}, ${listing.state} ${listing.zip_code}</p>
            <div class="detail-price">$${formatNumber(listing.price)}</div>

            <div class="detail-grid">
                <div class="detail-item">
                    <div class="label">Beds</div>
                    <div class="value">${listing.beds}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Baths</div>
                    <div class="value">${listing.baths}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Sq Ft</div>
                    <div class="value">${formatNumber(listing.sqft)}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Year Built</div>
                    <div class="value">${listing.year_built || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Stories</div>
                    <div class="value">${listing.stories || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Lot Size</div>
                    <div class="value">${listing.lot_sqft ? formatNumber(listing.lot_sqft) + ' sqft' : '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">HOA/Month</div>
                    <div class="value">${listing.hoa_monthly ? '$' + listing.hoa_monthly : 'None'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Days Listed</div>
                    <div class="value">${listing.days_on_market !== null ? listing.days_on_market : '-'}</div>
                </div>
            </div>

            <div class="detail-grid">
                <div class="detail-item">
                    <div class="label">Has Yard</div>
                    <div class="value">${listing.has_yard ? '✓ Yes' : 'No'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Has Pool</div>
                    <div class="value">${listing.has_pool ? '✓ Yes' : 'No'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Has Solar</div>
                    <div class="value">${listing.has_solar ? '✓ Yes' : 'No'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Crime Index</div>
                    <div class="value">${listing.crime_index || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Distance to Downtown</div>
                    <div class="value">${listing.distance_to_downtown ? listing.distance_to_downtown + ' mi' : '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Nearest Downtown</div>
                    <div class="value">${listing.nearest_downtown || '-'}</div>
                </div>
            </div>

            <div class="score-breakdown">
                <h3>Value Score: ${listing.value_score || '-'}</h3>
                <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 0.75rem;">
                    Score is calculated based on sqft/price, year built, location, HOA, yard, days on market, pool, and solar.
                </p>
                <div class="breakdown-item">
                    <span>Location (25%)</span>
                    <span>${listing.city || '-'}</span>
                </div>
                <div class="breakdown-item">
                    <span>Sq Ft per Dollar (23%)</span>
                    <span>${listing.sqft && listing.price ? (listing.sqft / listing.price * 1000).toFixed(1) + ' sqft/$1k' : '-'}</span>
                </div>
                <div class="breakdown-item">
                    <span>Year Built (20%)</span>
                    <span>${listing.year_built || '-'}</span>
                </div>
                <div class="breakdown-item">
                    <span>Low HOA (13%)</span>
                    <span>${listing.hoa_monthly ? '$' + listing.hoa_monthly + '/mo' : 'None ✓'}</span>
                </div>
                <div class="breakdown-item">
                    <span>Private Yard (10%)</span>
                    <span>${listing.has_yard ? '✓' : '-'}</span>
                </div>
                <div class="breakdown-item">
                    <span>Days on Market (3%)</span>
                    <span>${listing.days_on_market !== null ? listing.days_on_market + ' days' : '-'}</span>
                </div>
                <div class="breakdown-item">
                    <span>Pool (3%)</span>
                    <span>${listing.has_pool ? '✓' : '-'}</span>
                </div>
                <div class="breakdown-item">
                    <span>Solar (3%)</span>
                    <span>${listing.has_solar ? '✓' : '-'}</span>
                </div>
            </div>

            ${listing.url ? `<a href="${listing.url}" target="_blank" rel="noopener" class="view-listing-btn">View on Redfin →</a>` : ''}
        </div>
    `;

    elements.modalBody.html(html);
    elements.modal.removeClass('hidden');
}

function closeModal() {
    elements.modal.addClass('hidden');
}

function exportCSV() {
    window.location.href = '/api/export';
}

function showLoading(show) {
    if (show) {
        elements.loadingEl.removeClass('hidden');
    } else {
        elements.loadingEl.addClass('hidden');
    }
}

function showError(message) {
    elements.errorEl.text(message).removeClass('hidden');
}

function hideError() {
    elements.errorEl.addClass('hidden');
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
