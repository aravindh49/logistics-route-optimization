const API_URL = '';

const dom = {
    startSelect: document.getElementById('start-city'),
    endSelect: document.getElementById('end-city'),
    optimizeBtn: document.getElementById('optimize-btn'),
    resultsPanel: document.getElementById('results-panel'),
    kpiSaved: document.getElementById('kpi-saved'),
    kpiBaseline: document.getElementById('kpi-baseline'),
    kpiOptimized: document.getElementById('kpi-optimized'),
    kpiBaseCost: document.getElementById('kpi-base-cost'),
    kpiOptCost: document.getElementById('kpi-opt-cost'),
    kpiCostSaved: document.getElementById('kpi-cost-saved'),
    kpiEfficiency: document.getElementById('kpi-efficiency'),
    downloadBtn: document.getElementById('download-btn')
};

let map, baselineLayer, optimizedLayer;
let currentResult = null;
let cityMarkers = {};

async function init() {
    // Initialize Leaflet Map (Centered on US)
    map = L.map('map-visual').setView([39.8283, -98.5795], 4);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    try {
        const response = await axios.get(`${API_URL}/cities`);
        const cities = response.data.cities;

        cities.forEach(city => {
            // Add to dropdowns
            const option = new Option(city.name, city.name);
            dom.startSelect.add(option.cloneNode(true));
            dom.endSelect.add(new Option(city.name, city.name));

            // Add Marker to Map
            const marker = L.marker([city.lat, city.lon]).addTo(map);
            marker.bindPopup(`<b>${city.name}</b><br>Click to set as Start/End`);
            marker.on('click', () => handleMarkerClick(city.name));
            cityMarkers[city.name] = marker;
        });
    } catch (error) {
        console.error('Failed to load cities', error);
        alert('Could not connect to API. Make sure the backend is running.');
    }
}

function handleMarkerClick(cityName) {
    if (dom.startSelect.value === "") {
        dom.startSelect.value = cityName;
    } else if (dom.endSelect.value === "") {
        dom.endSelect.value = cityName;
    } else {
        // Reset and start over
        dom.startSelect.value = cityName;
        dom.endSelect.value = "";
    }
}

dom.optimizeBtn.addEventListener('click', async () => {
    const start = dom.startSelect.value;
    const end = dom.endSelect.value;

    if (!start || !end) {
        alert('Please select both Origin and Destination');
        return;
    }

    if (start === end) {
        alert('Origin and Destination cannot be the same');
        return;
    }

    // Set Loading State
    setLoading(true);

    try {
        const response = await axios.post(`${API_URL}/optimize`, {
            start_node: start,
            end_node: end
        });

        currentResult = response.data;
        displayResults(currentResult);
    } catch (error) {
        console.error(error);
        alert('Optimization failed. Try different cities.');
    } finally {
        setLoading(false);
    }
});

function setLoading(isLoading) {
    if (isLoading) {
        dom.optimizeBtn.disabled = true;
        dom.optimizeBtn.textContent = 'Optimizing...';
    } else {
        dom.optimizeBtn.disabled = false;
        dom.optimizeBtn.textContent = 'Find Optimized Route';
    }
}

function displayResults(data) {
    // Clear previous lines
    if (baselineLayer) map.removeLayer(baselineLayer);
    if (optimizedLayer) map.removeLayer(optimizedLayer);

    // Draw Baseline (Dashed Orange)
    if (data.base_coords && data.base_coords.length > 0) {
        baselineLayer = L.polyline(data.base_coords, {
            color: '#f59e0b',
            weight: 3,
            dashArray: '10, 10',
            opacity: 0.7
        }).addTo(map);
    }

    // Draw Optimized (Solid Green)
    if (data.opt_coords && data.opt_coords.length > 0) {
        optimizedLayer = L.polyline(data.opt_coords, {
            color: '#10b981',
            weight: 5,
            opacity: 0.9
        }).addTo(map);
    }

    // Fit map to show both routes
    const allCoords = [...data.base_coords, ...data.opt_coords];
    if (allCoords.length > 0) {
        map.fitBounds(L.latLngBounds(allCoords), { padding: [50, 50] });
    }

    // Update KPIs
    animateValue(dom.kpiSaved, data.time_saved, ' min');
    animateValue(dom.kpiBaseline, data.baseline_time, ' min');
    animateValue(dom.kpiOptimized, data.optimized_time, ' min');

    // Cost KPIs
    animateValue(dom.kpiBaseCost, '$' + data.baseline_cost, '');
    animateValue(dom.kpiOptCost, '$' + data.optimized_cost, '');
    animateValue(dom.kpiCostSaved, '$' + data.cost_saved, '');

    animateValue(dom.kpiEfficiency, data.efficiency_gain, '%');

    // Show Panel
    dom.resultsPanel.classList.remove('hidden');
}

function animateValue(element, value, unit) {
    element.textContent = value + unit;
    // Simple animation could be added here
}

dom.downloadBtn.addEventListener('click', () => {
    if (!currentResult) return;

    const params = new URLSearchParams({
        start_node: currentResult.start_node,
        end_node: currentResult.end_node,
        opt_time: currentResult.optimized_time,
        base_time: currentResult.baseline_time
    });

    window.open(`${API_URL}/report?${params.toString()}`, '_blank');
});

// Initialize
init();
