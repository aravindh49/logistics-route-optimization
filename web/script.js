// Modern Robust Script for Logistics Optimization
// Ensures Map Stability and Clean API Interactions

// Configuration
const API_URL = window.location.origin;
const DEFAULT_CENTER = [11.1271, 78.6569]; // Tamil Nadu
const DEFAULT_ZOOM = 7;

// DOM Elements Reference
const els = {
    startSelect: document.getElementById('start-city'),
    endSelect: document.getElementById('end-city'),
    optimizeBtn: document.getElementById('optimize-btn'),
    resultsPanel: document.getElementById('results-panel'),
    downloadBtn: document.getElementById('download-btn'),
    // Outputs
    valTimeSaved: document.getElementById('val-time-saved'),
    valBaseTime: document.getElementById('val-base-time'),
    valOptTime: document.getElementById('val-opt-time'),
    valBaseCost: document.getElementById('val-base-cost'),
    valOptCost: document.getElementById('val-opt-cost'),
    valEfficiency: document.getElementById('val-efficiency'),
};

// Global State
let map;
let layers = {
    baseline: null,
    optimized: null,
    markers: []
};
let currentResults = null;

// --- Initialization ---
async function initApp() {
    console.log("🚀 Starting Application...");

    // 1. Initialize Map
    initMap();

    // 2. Load Cities
    await loadCities();

    // 3. Attach Event Listeners
    setupEventListeners();
}

// --- Map Logic ---
function initMap() {
    console.log("🗺️ Initializing Leaflet Map...");

    const mapContainer = document.getElementById('map-visual');
    if (!mapContainer) return console.error("Map container not found!");

    // Create Map
    map = L.map(mapContainer).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    // Standard OpenStreetMap Tiles (Keyless, Public, Reliable)
    // Note: Dark Mode is handled by CSS Filter in style.css
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // ROBUST RESIZE HANDLER: This is the magic fix for "Grey Map" issues
    // It watches the container size and tells Leaflet to redraw if it changes
    const resizeObserver = new ResizeObserver(() => {
        map.invalidateSize();
    });
    resizeObserver.observe(mapContainer);

    // Fallback force redraws
    setTimeout(() => map.invalidateSize(), 500);
    setTimeout(() => map.invalidateSize(), 2000);

    console.log("✅ Map Initialized");
}

async function loadCities() {
    try {
        const res = await axios.get(`${API_URL}/cities`);
        const cities = res.data.cities;

        // Add Markers and Fill Dropdowns
        cities.forEach(city => {
            // Dropdown Option
            els.startSelect.add(new Option(city.name, city.name));
            els.endSelect.add(new Option(city.name, city.name));

            // Map Marker
            const marker = L.marker([city.lat, city.lon]).addTo(map);
            marker.bindPopup(`<b>${city.name}</b>`);
            marker.on('click', () => {
                // Auto-select logic
                if (els.startSelect.value === "") els.startSelect.value = city.name;
                else els.endSelect.value = city.name;
            });
            layers.markers.push(marker);
        });

    } catch (error) {
        console.error("Failed to load cities:", error);
        alert("Cannot connect to Server. Is the backend running?");
    }
}

// --- Interaction Logic ---
function setupEventListeners() {
    els.optimizeBtn.addEventListener('click', async () => {
        const start = els.startSelect.value;
        const end = els.endSelect.value;

        if (!start || !end) return alert("Please select both Origin and Destination.");
        if (start === end) return alert("Start and End cities cannot be the same.");

        // UI State: Loading
        els.optimizeBtn.textContent = "Processing AI Optimization...";
        els.optimizeBtn.disabled = true;

        try {
            // Call API
            const res = await axios.post(`${API_URL}/optimize`, {
                start_node: start,
                end_node: end
            });

            // Handle Success
            currentResults = res.data;
            displayResults(currentResults);

        } catch (error) {
            console.error(error);
            alert("Optimization failed. Please try again.");
        } finally {
            // UI State: Ready
            els.optimizeBtn.textContent = "Find Optimized Route";
            els.optimizeBtn.disabled = false;
        }
    });

    els.downloadBtn.addEventListener('click', () => {
        if (!currentResults) return;
        const params = new URLSearchParams({
            start_node: currentResults.start_node,
            end_node: currentResults.end_node,
            opt_time: currentResults.optimized_time,
            base_time: currentResults.baseline_time,
            opt_cost: currentResults.optimized_cost,
            base_cost: currentResults.baseline_cost,
            time_eff: currentResults.time_efficiency,
            cost_eff: currentResults.cost_efficiency,
            ai_score: currentResults.ai_score,
            base_score: currentResults.baseline_score
        });
        window.open(`${API_URL}/report?${params.toString()}`, '_blank');
    });
}

// --- Visualization Logic ---
function displayResults(data) {
    // 1. Clear Old Layers
    if (layers.baseline) map.removeLayer(layers.baseline);
    if (layers.optimized) map.removeLayer(layers.optimized);

    // 2. Draw Baseline (Orange thick border)
    if (data.base_coords && data.base_coords.length > 0) {
        layers.baseline = L.polyline(data.base_coords, {
            color: '#f59e0b', // Orange
            weight: 12,       // Thick enough to be seen under the green line
            opacity: 0.5
        }).addTo(map);
    }

    // 3. Draw Optimized (Green Solid inner line)
    if (data.opt_coords && data.opt_coords.length > 0) {
        layers.optimized = L.polyline(data.opt_coords, {
            color: '#10b981', // Green
            weight: 4,        // Thinner, sits strictly on top of orange
            opacity: 1
        }).addTo(map);
    }

    // 4. Fit Map View
    const allPoints = [...data.base_coords, ...data.opt_coords];
    if (allPoints.length > 0) {
        map.fitBounds(L.latLngBounds(allPoints), { padding: [50, 50] });
    }

    // 5. Update Metrics
    els.valTimeSaved.textContent = `${data.time_saved} min`;
    els.valBaseTime.textContent = `${data.baseline_time} min`;
    els.valOptTime.textContent = `${data.optimized_time} min`;

    els.valBaseCost.textContent = `$${data.baseline_cost}`;
    els.valOptCost.textContent = `$${data.optimized_cost}`;

    document.getElementById('val-time-eff').textContent = `+${data.time_efficiency}%`;
    document.getElementById('val-cost-eff').textContent = `+${data.cost_efficiency}%`;
    document.getElementById('val-base-score').textContent = `${data.baseline_score}`;
    document.getElementById('val-opt-score').textContent = `${data.ai_score}`;

    // 6. Show Panel
    els.resultsPanel.classList.remove('hidden');
}

// Start
initApp();
