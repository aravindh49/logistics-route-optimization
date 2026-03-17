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
    
    // New Features
    simRain: document.getElementById('sim-rain'),
    simAccident: document.getElementById('sim-accident'),
    simRush: document.getElementById('sim-rush'),
    vehicleType: document.getElementById('vehicle-type'),
    stopsContainer: document.getElementById('stops-container'),
    addStopBtn: document.getElementById('add-stop-btn'),
    valCo2: document.getElementById('val-co2'),
};

// Global State
let map;
let layers = {
    baseline: null,
    optimized: null,
    markers: {} // Change to object for fast lookup
};

const LeafIcon = L.Icon.extend({
    options: {
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    }
});

const mapIcons = {
    default: new LeafIcon({iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png'}),
    start: new LeafIcon({iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png'}),
    end: new LeafIcon({iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png'}),
    stop: new LeafIcon({iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png'})
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
    // Store loaded cities for generating stops dropdowns
    window.cityOptions = '';
    
    try {
        const res = await axios.get(`${API_URL}/cities`);
        const cities = res.data.cities;

        // Add Markers and Fill Dropdowns
        cities.forEach(city => {
            const optionHTML = `<option value="${city.name}">${city.name}</option>`;
            window.cityOptions += optionHTML;
            
            // Dropdown Option
            els.startSelect.add(new Option(city.name, city.name));
            els.endSelect.add(new Option(city.name, city.name));

            // Map Marker
            const marker = L.marker([city.lat, city.lon], {icon: mapIcons.default}).addTo(map);
            marker.bindPopup(`<b>${city.name}</b>`);
            marker.on('click', () => {
                // Auto-select logic
                if (els.startSelect.value === "") els.startSelect.value = city.name;
                else els.endSelect.value = city.name;
            });
            layers.markers[city.name] = marker;
        });

    } catch (error) {
        console.error("Failed to load cities:", error);
        alert("Cannot connect to Server. Is the backend running?");
    }
}

// --- Interaction Logic ---
function setupEventListeners() {
    // Add Stop Button Logic
    els.addStopBtn.addEventListener('click', () => {
        const stopDiv = document.createElement('div');
        stopDiv.className = 'input-group stop-group';
        stopDiv.style.marginBottom = '0.5rem';
        stopDiv.style.display = 'flex';
        stopDiv.style.gap = '0.5rem';
        
        stopDiv.innerHTML = `
            <select class="stop-city" style="flex:1;">
                <option value="" disabled selected>Select Stop...</option>
                ${window.cityOptions}
            </select>
            <button class="btn-remove-stop" style="background:#ef4444; color:white; border:none; border-radius:8px; padding:0 0.8rem; cursor:pointer;" onclick="this.parentElement.remove()">X</button>
        `;
        els.stopsContainer.appendChild(stopDiv);
    });

    els.optimizeBtn.addEventListener('click', async () => {
        const start = els.startSelect.value;
        const end = els.endSelect.value;

        if (!start || !end) return alert("Please select both Origin and Destination.");
        if (start === end) return alert("Start and End cities cannot be the same.");

        // Gather stops
        const stopSelects = document.querySelectorAll('.stop-city');
        const stops = Array.from(stopSelects).map(s => s.value).filter(val => val !== "");

        // Gather scenario settings
        const scenario = {
            heavy_rain: els.simRain.checked,
            accident_zone: els.simAccident.checked,
            rush_hour: els.simRush.checked
        };
        const vehicle_type = els.vehicleType.value;

        // UI State: Loading
        els.optimizeBtn.textContent = "Processing AI Optimization...";
        els.optimizeBtn.disabled = true;

        try {
            let res;
            if (stops.length > 0) {
                // Call Multi-Stop API
                res = await axios.post(`${API_URL}/optimize-multi`, {
                    origin: start,
                    destination: end,
                    stops: stops,
                    vehicle_type: vehicle_type,
                    scenario: scenario
                });
            } else {
                // Call Single-Stop API
                res = await axios.post(`${API_URL}/optimize-single`, {
                    start_node: start,
                    end_node: end,
                    vehicle_type: vehicle_type,
                    scenario: scenario
                });
            }

            // Handle Success
            currentResults = res.data;
            currentResults.vehicle_type = vehicle_type;
            if(stops.length > 0) {
                currentResults.is_multi = true;
                currentResults.stops = stops;
            }
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

    // Normalize paths based on Single vs Multi response formats
    const bCoords = data.base_coords || [];
    const optCoords = data.opt_coords || data.optimized_path_coords || [];

    // Adjust Marker Colors
    Object.values(layers.markers).forEach(m => m.setIcon(mapIcons.default)); // Reset all
    if (layers.markers[data.start_node]) layers.markers[data.start_node].setIcon(mapIcons.start);
    if (layers.markers[data.end_node]) layers.markers[data.end_node].setIcon(mapIcons.end);
    if (data.is_multi && data.stops) {
        data.stops.forEach(s => {
            if (layers.markers[s]) layers.markers[s].setIcon(mapIcons.stop);
        });
    }

    // 2. Draw Baseline (Orange thick border)
    if (bCoords.length > 0) {
        layers.baseline = L.polyline(bCoords, {
            color: '#f59e0b', // Orange
            weight: 12,       // Thick enough to be seen under the green line
            opacity: 0.5
        }).addTo(map);
    }

    // 3. Draw Optimized (Green/Cyan Animated inner line)
    if (optCoords.length > 0) {
        const isElectric = data.vehicle_type === 'electric';
        layers.optimized = L.polyline(optCoords, {
            color: isElectric ? '#0ea5e9' : '#10b981', // Blueish cyan for electric, green for diesel
            weight: 4,        // Thinner, sits strictly on top of orange
            opacity: 1,
            className: isElectric ? 'route-electric' : 'route-diesel'
        }).addTo(map);
    }

    // 4. Fit Map View
    const allPoints = [...bCoords, ...optCoords];
    if (allPoints.length > 0) {
        map.fitBounds(L.latLngBounds(allPoints), { padding: [50, 50] });
    }

    // 5. Update Metrics Safely
    els.valTimeSaved.textContent = `${data.time_saved} min`;
    els.valBaseTime.textContent = `${data.baseline_time} min`;
    els.valOptTime.textContent = `${data.optimized_time} min`;

    els.valBaseCost.textContent = data.is_multi ? `${data.baseline_cost} L` : `$${data.baseline_cost}`;
    els.valOptCost.textContent = data.is_multi ? `${data.optimized_cost} L` : `$${data.optimized_cost}`;

    document.getElementById('val-time-eff').textContent = data.time_efficiency > 0 ? `+${data.time_efficiency}%` : `${data.time_efficiency}%`;
    document.getElementById('val-cost-eff').textContent = data.cost_efficiency > 0 ? `+${data.cost_efficiency}%` : `${data.cost_efficiency}%`;
    document.getElementById('val-base-score').textContent = `${data.baseline_score}`;
    document.getElementById('val-opt-score').textContent = `${data.ai_score}`;

    if (els.valCo2) {
        els.valCo2.textContent = `${data.co2_emission} kg`;
    }

    // 6. Show Panel
    els.resultsPanel.classList.remove('hidden');
}

// Start
initApp();
