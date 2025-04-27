import json
import os
import random
import math

def create_leaflet_map(forecasts, output_path):
    """
    Write a Leaflet+D3 HTML visualization for submarine forecasts with Monte-Carlo simulation.
    Embeds the forecast data as a JS variable in the HTML.
    """
    # forecasts is expected to be a dict with keys: central_path, forecast_path, etc.
    forecast_json = json.dumps(forecasts, indent=2)
    num_subs = len(forecasts)
    if num_subs == 0:
        sub_message = "No submarines to display."
    elif num_subs == 1:
        sub_message = "Tracking 1 Jin-Class (Type 094) Nuclear Submarine"
    else:
        sub_message = f"Tracking {num_subs} Jin-Class (Type 094) Nuclear Submarines"

    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jin-Class SSBN Monte-Carlo Tracker</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/@turf/turf@6.5.0/turf.min.js"></script>
    <script src="https://unpkg.com/@ansur/leaflet-pulse-icon@0.1.1/dist/L.Icon.Pulse.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <link rel="stylesheet" href="https://unpkg.com/@ansur/leaflet-pulse-icon@0.1.1/dist/L.Icon.Pulse.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.js"></script>
    <style>
        :root {{ --accent: #198754; /* green */ }}
        body, html {{ 
            margin: 0; 
            padding: 0;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            font-family: system-ui, sans-serif; 
        }}
        #map {{ 
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            height: 100%;
            width: 100%;
        }}
        .controls {{ 
            position: absolute; 
            top: 20px; 
            right: 20px; 
            z-index: 1000; 
            background: white; 
            padding: 15px; 
            border-radius: 8px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.3); 
            min-width: 240px;
        }}
        .controls h3 {{
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 18px;
            color: #333;
        }}
        .submarine-info {{
            margin-bottom: 15px;
            font-weight: 500;
        }}
        .submarine-marker {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .naval-base {{
            background-color: #ff5722;
            border-radius: 50%;
            width: 12px;
            height: 12px;
            border: 2px solid white;
            box-shadow: 0 0 4px rgba(0,0,0,0.5);
        }}
        .path-line {{ 
            stroke: var(--accent); 
            stroke-width: 2; 
            stroke-dasharray: 6, 4; 
        }}
        .uncertainty-ring {{
            stroke: var(--accent);
            stroke-width: 1;
            fill: none;
            opacity: 0.5;
        }}
        button {{ 
            padding: 8px 12px; 
            margin: 5px 0; 
            cursor: pointer; 
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 4px;
            font-weight: 500;
            transition: background-color 0.2s;
            width: 100%;
            text-align: left;
        }}
        button.active {{
            background: #0d6efd;
        }}
        button:hover {{
            opacity: 0.9;
        }}
        .legend {{ 
            position: absolute; 
            bottom: 30px; 
            left: 10px; 
            z-index: 1000; 
            background: white; 
            padding: 12px; 
            border-radius: 8px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.3); 
            font-size: 12px; 
        }}
        .legend-item {{ 
            display: flex; 
            align-items: center; 
            margin-bottom: 6px; 
        }}
        .legend-color {{ 
            display: inline-block; 
            width: 15px; 
            height: 15px; 
            margin-right: 8px; 
            border-radius: 50%; 
        }}
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        /* Improved line styles */
        .historical-path {{
            stroke-width: 4;
            opacity: 0.8;
        }}
        .forecast-path {{
            stroke-width: 3;
            stroke-dasharray: 10, 5;
            opacity: 0.7;
        }}
        /* Timeline slider styling */
        #time-control {{
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            width: 60%;
            height: 40px;
            z-index: 1000;
            background: white;
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 0 15px rgba(0,0,0,0.3);
        }}
        #timeline {{
            height: 10px;
            margin-bottom: 5px;
        }}
        .time-display {{
            text-align: center;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 5px;
        }}
        .play-controls {{
            display: flex;
            justify-content: center;
            margin-top: 5px;
        }}
        .play-controls button {{
            width: auto;
            margin: 0 5px;
            padding: 4px 10px;
            font-size: 12px;
        }}
        .noUi-connect {{
            background: var(--accent);
        }}
        /* Monte Carlo uncertainty visualization */
        .uncertainty-cone {
            opacity: 0.2;
        }
        .time-step-marker {
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border-radius: 50%;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
            box-shadow: 0 0 5px rgba(0,0,0,0.5);
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="controls">
        <h3>Jin-Class SSBN Fleet Control</h3>
        <div class="submarine-info">
            {sub_message}
        </div>
        <button id="toggle-simulations" class="active">Hide Simulations</button>
        <button id="toggle-history" class="active">Hide History</button>
        <button id="toggle-uncertainty" class="active">Hide Uncertainty</button>
        <button id="reset">Reset View</button>
    </div>
    <div class="legend">
        <div class="legend-item">
            <span class="legend-color" style="background-color: #ff5722;"></span>
            <span>Naval Base</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: var(--accent);"></span>
            <span>Current Position</span>
        </div>
        <div class="legend-item">
            <span style="height: 4px; background-color: #0d6efd; width: 15px; display: inline-block;"></span>
            <span>Historical Track</span>
        </div>
        <div class="legend-item">
            <span style="height: 3px; border-top: 3px dashed #e91e63; width: 15px; display: inline-block;"></span>
            <span>Forecast Path</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: rgba(25, 135, 84, 0.2);"></span>
            <span>Uncertainty Cone</span>
        </div>
        <div class="legend-item">
            <span style="display: inline-block; width: 15px; height: 15px; border: 1px solid #666; border-radius: 50%;"></span>
            <span>Time Step Uncertainty</span>
        </div>
    </div>
    
    <div id="time-control">
        <div class="time-display">Simulation Time: <span id="current-time">T+0h</span></div>
        <div id="timeline"></div>
        <div class="play-controls">
            <button id="play-pause">▶ Play</button>
            <button id="reset-time">Reset</button>
        </div>
    </div>
    
    <div class="loading">Loading map...</div>
    <script>
        // Wait for all resources to load
        window.addEventListener('load', function() {{
            // Hide loading message
            document.querySelector('.loading').style.display = 'none';
            
            // Submarine forecast data from Python
            window.submarineForecasts = {forecast_json};
            
            // Naval bases - key locations where submarines can dock
            const navalBases = [
                {{ name: "Yulin Naval Base", coords: [18.229, 109.706] }},  // Hainan Island
                {{ name: "Qingdao Base", coords: [36.071, 120.418] }},       // North China
                {{ name: "Ningbo Base", coords: [29.868, 122.108] }},        // East China
                {{ name: "Xiamen Base", coords: [24.455, 118.082] }},        // South China
                {{ name: "Xiaopingdao Base", coords: [38.822, 121.536] }}    // Submarine pen
            ];
            
            // Simple waypoints to avoid land masses - strategic points in the sea
            const seaWaypoints = [
                // South China Sea
                {{ name: "SCS1", coords: [16.0, 114.0] }},
                {{ name: "SCS2", coords: [13.2, 117.4] }}, 
                {{ name: "SCS3", coords: [20.5, 118.7] }},
                // East China Sea
                {{ name: "ECS1", coords: [27.5, 123.6] }},
                {{ name: "ECS2", coords: [31.3, 125.8] }},
                // Yellow Sea
                {{ name: "YS1", coords: [35.6, 122.5] }},
                // Taiwan Strait
                {{ name: "TS1", coords: [23.2, 119.8] }},
                // Philippine Sea
                {{ name: "PS1", coords: [22.0, 126.0] }},
                {{ name: "PS2", coords: [18.0, 128.0] }}
            ];

            // Function to create Monte Carlo uncertainty circles
            function createUncertaintyCircles(center, timeStepHours, uncertaintyRadiusKm, color) {{
                // Create a series of concentric circles representing uncertainty
                const rings = [];
                
                // Create five rings of increasing uncertainty
                const numRings = 5;
                for (let i = 1; i <= numRings; i++) {{
                    const radius = (uncertaintyRadiusKm / numRings) * i;
                    const circle = L.circle(center, {{
                        radius: radius * 1000, // Convert to meters
                        color: color,
                        weight: 1,
                        fillColor: color,
                        fillOpacity: 0.05,
                        dashArray: '3, 5'
                    }});
                    rings.push(circle);
                }}
                
                // Add a time step marker at the center
                const icon = L.divIcon({{
                    className: 'time-step-marker',
                    html: `T+${{timeStepHours}}h`,
                    iconSize: [40, 40]
                }});
                
                const marker = L.marker(center, {{ icon }});
                rings.push(marker);
                
                return rings;
            }}

            try {{
                // Initialize map with retina support
                const map = L.map('map', {{ 
                    minZoom: 3, 
                    detectRetina: true,
                    zoomControl: true,
                    attributionControl: true
                }}).setView([21, 115], 5);
                
                // Add standard OpenStreetMap tiles with error handling
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19,
                    attribution: '© OpenStreetMap',
                    errorTileUrl: 'https://tile.openstreetmap.org/0/0/0.png'
                }}).addTo(map);

                // Create layer groups for better organization
                const histLayer = L.layerGroup().addTo(map);
                const fcastLayer = L.layerGroup().addTo(map);
                const uncertaintyLayer = L.layerGroup().addTo(map);
                const baseLayer = L.layerGroup().addTo(map);
                const posLayer = L.layerGroup().addTo(map);
                const timeStepLayer = L.layerGroup().addTo(map);

                // Add naval bases to the map
                navalBases.forEach(base => {{
                    const marker = L.marker(base.coords, {{
                        icon: L.divIcon({{
                            className: 'naval-base',
                            iconSize: [12, 12]
                        }})
                    }})
                    .bindTooltip(base.name, {{ permanent: false }})
                    .addTo(baseLayer);
                }});
                
                // Store simulation state
                const simState = {{
                    timeIndex: 0,
                    maxTimeIndex: 0,
                    isPlaying: false,
                    playInterval: null,
                    speed: 1000, // ms between steps
                    submarinePositions: {{}}
                }};

                // Create markers and visualizations
                const submarineMarkers = {{}};
                const submarinePaths = {{}};
                const submarineHistoryPaths = {{}};
                const uncertaintyCones = {{}};
                const timeStepMarkers = {{}};

                // Find best route between points that avoids land by using naval waypoints
                function findSeaRoute(start, end) {{
                    // Find closest waypoints/bases to start and end
                    const allPoints = [...navalBases, ...seaWaypoints];
                    
                    // Simple algorithm to find a path using waypoints
                    // In a real application, this would use a marine routing API or algorithm
                    
                    // Convert start/end to [lat, lon] format
                    const startPoint = [start[1], start[0]];
                    const endPoint = [end[1], end[0]];
                    
                    // If start and end are close enough, just go direct
                    const distance = turf.distance(
                        turf.point([start[0], start[1]]), 
                        turf.point([end[0], end[1]]), 
                        {{units: 'kilometers'}}
                    );
                    
                    if (distance < 300) {{
                        return [startPoint, endPoint];
                    }}
                    
                    // Find if we're starting from a base
                    const startBase = navalBases.find(base => 
                        turf.distance(
                            turf.point([start[0], start[1]]), 
                            turf.point([base.coords[1], base.coords[0]]), 
                            {{units: 'kilometers'}}
                        ) < 50
                    );
                    
                    // Find if we're ending at a base
                    const endBase = navalBases.find(base => 
                        turf.distance(
                            turf.point([end[0], end[1]]), 
                            turf.point([base.coords[1], base.coords[0]]), 
                            {{units: 'kilometers'}}
                        ) < 50
                    );
                    
                    // Get appropriate waypoints based on geographic regions
                    // Simplified approach - in a full implementation would use proper marine routing
                    let waypoints = [];
                    
                    // Based on start/end location, choose appropriate waypoints
                    // This is a very simplified version and would need to be enhanced
                    // with proper marine routing for a production application
                    
                    if (startBase || endBase) {{
                        // If either point is at a naval base, find appropriate sea waypoints
                        if (start[1] < 25 && end[1] < 25) {{
                            // South China Sea route
                            waypoints = [seaWaypoints[0], seaWaypoints[1]];
                        }} else if (start[1] > 30 && end[1] > 30) {{
                            // Yellow Sea route
                            waypoints = [seaWaypoints[5]];
                        }} else {{
                            // East China Sea route
                            waypoints = [seaWaypoints[3], seaWaypoints[4]];
                        }}
                    }}
                    
                    // Build the route
                    const route = [startPoint];
                    
                    // Add waypoints if relevant
                    if (waypoints.length > 0) {{
                        waypoints.forEach(wp => {{
                            route.push([wp.coords[0], wp.coords[1]]);
                        }});
                    }}
                    
                    route.push(endPoint);
                    return route;
                }}

                // Initialize timeline data
                let timelineData = {{
                    minTime: 0,
                    maxTime: 0,
                    timeSteps: []
                }};

                if (Object.keys(window.submarineForecasts).length === 0) {{
                    // No subs: show a message overlay
                    const noDataDiv = document.createElement('div');
                    noDataDiv.style.position = 'absolute';
                    noDataDiv.style.top = '50%';
                    noDataDiv.style.left = '50%';
                    noDataDiv.style.transform = 'translate(-50%, -50%)';
                    noDataDiv.style.background = 'rgba(255,255,255,0.95)';
                    noDataDiv.style.padding = '2em 3em';
                    noDataDiv.style.borderRadius = '10px';
                    noDataDiv.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
                    noDataDiv.style.fontSize = '1.3em';
                    noDataDiv.innerText = 'No submarine forecast data available.';
                    document.body.appendChild(noDataDiv);
                    
                    // Hide the timeline control
                    document.getElementById('time-control').style.display = 'none';
                }} else {{
                    // Assign custom colors for different submarines
                    const submarineColors = [
                        '#0d6efd', // blue
                        '#e91e63', // pink
                        '#9c27b0', // purple
                        '#ff9800', // orange
                        '#8bc34a', // light green
                        '#795548'  // brown
                    ];
                    
                    // Process forecast data to extract time steps
                    Object.entries(window.submarineForecasts).forEach(([id, data], idx) => {{
                        if (data.forecast_times && data.forecast_times.length > 0) {{
                            // Add times to our timeline data if not already present
                            data.forecast_times.forEach(time => {{
                                if (!timelineData.timeSteps.includes(time)) {{
                                    timelineData.timeSteps.push(time);
                                }}
                            }});
                        }}
                    }});
                    
                    // Sort and clean up time steps
                    timelineData.timeSteps.sort((a, b) => a - b);
                    timelineData.minTime = timelineData.timeSteps[0] || 0;
                    timelineData.maxTime = timelineData.timeSteps[timelineData.timeSteps.length - 1] || 0;
                    simState.maxTimeIndex = timelineData.timeSteps.length - 1;
                    
                    // Process and visualize each submarine
                    Object.entries(window.submarineForecasts).forEach(([id, data], idx) => {{
                        try {{
                            // Use our custom color scheme
                            const color = submarineColors[idx % submarineColors.length];
                            
                            // Create submarine marker at last known position with pulse effect
                            const lastPos = data.central_path[data.central_path.length - 1];
                            const pulseIcon = L.icon.pulse({{
                                iconSize: [14, 14],
                                color: color,
                                fillColor: color,
                                animate: true
                            }});
                            
                            const marker = L.marker([lastPos[1], lastPos[0]], {{
                                icon: pulseIcon
                            }}).addTo(posLayer)
                            .bindPopup(`
                                <strong>Jin${{idx+1}}</strong><br>
                                Last seen: 2025-03-15 11:45<br>
                                Status: In Port<br>
                                Position: ${{lastPos[1].toFixed(4)}}, ${{lastPos[0].toFixed(4)}}
                            `);
                            submarineMarkers[id] = marker;
                            
                            // Store position data for timeline animation
                            simState.submarinePositions[id] = {{
                                color: color,
                                positions: [],
                                marker: marker
                            }};

                            // Draw historical path (solid line) with sea routing
                            if (data.history_path && data.history_path.length > 1) {{
                                // Create enhanced sea routes for historical path
                                let seaRoutedPath = [];
                                for (let i = 0; i < data.history_path.length - 1; i++) {{
                                    const segment = findSeaRoute(data.history_path[i], data.history_path[i+1]);
                                    seaRoutedPath = seaRoutedPath.concat(segment);
                                }}
                                
                                const historyLine = L.polyline(seaRoutedPath, {{
                                    color: color,
                                    weight: 4,
                                    opacity: 0.8,
                                    className: 'historical-path',
                                    smoothFactor: 1
                                }}).addTo(histLayer);
                                
                                submarineHistoryPaths[id] = historyLine;
                            }}

                            // Draw forecasted path (dashed line) with sea routing
                            if (data.forecast_path && data.forecast_path.length > 0) {{
                                // Make sure we have history_path before accessing it
                                let startPoint = data.history_path && data.history_path.length > 0 ? 
                                    data.history_path[data.history_path.length-1] : data.central_path[data.central_path.length-1];
                                
                                // Create sea-routed forecast path
                                let seaRoutedForecast = [];
                                
                                // Start from last known position
                                let lastPoint = startPoint;
                                
                                // Connect with each forecast point using sea routing
                                data.forecast_path.forEach((forecastPoint, idx) => {{
                                    const segment = findSeaRoute(lastPoint, forecastPoint);
                                    seaRoutedForecast = seaRoutedForecast.concat(segment);
                                    lastPoint = forecastPoint;
                                    
                                    // Add position data for timeline animation
                                    // Fix: Store coordinates with proper indexing
                                    const timeIndex = idx < data.forecast_times.length ? idx : 0;
                                    simState.submarinePositions[id].positions.push({{
                                        coords: [forecastPoint[1], forecastPoint[0]],
                                        timeIndex: timeIndex
                                    }});
                                }});
                                
                                const forecastLine = L.polyline(seaRoutedForecast, {{
                                    color: color,
                                    weight: 3,
                                    dashArray: '10, 5',
                                    opacity: 0.7,
                                    className: 'forecast-path',
                                    smoothFactor: 1
                                }}).addTo(fcastLayer);
                                
                                submarinePaths[id] = forecastLine;
                            }}

                            // Create uncertainty cone with improved styling
                            if (data.cone_polygon && data.cone_polygon.length > 1) {{
                                const cone = L.polygon(data.cone_polygon.map(p => [p[1], p[0]]), {{
                                    color: color,
                                    weight: 1,
                                    fillColor: color,
                                    fillOpacity: 0.15,
                                    smoothFactor: 1,
                                    className: 'uncertainty-cone'
                                }}).addTo(uncertaintyLayer);
                                
                                uncertaintyCones[id] = cone;
                            }}
                            
                            // Create Monte Carlo uncertainty time step markers
                            if (data.forecast_path && data.forecast_times) {{
                                timeStepMarkers[id] = [];
                                
                                data.forecast_path.forEach((p, idx) => {{
                                    if (idx < data.forecast_times.length) {{
                                        // Calculate uncertainty that increases with time
                                        // Base uncertainty radius starts at 10km and increases by 8km per time step
                                        const uncertaintyRadius = 10 + (idx * 8);
                                        const timeStepHours = data.forecast_times[idx];
                                        
                                        // Create time step markers with uncertainty circles
                                        const center = [p[1], p[0]];
                                        const circles = createUncertaintyCircles(center, timeStepHours, uncertaintyRadius, color);
                                        
                                        // Add to the layer group
                                        const circleGroup = L.layerGroup(circles).addTo(timeStepLayer);
                                        timeStepMarkers[id].push(circleGroup);
                                    }}
                                }});
                            }}
                        }} catch (e) {{
                            console.error(`Error processing submarine ${{id}}:`, e);
                        }}
                    }});
                    
                    // Initialize timeline slider
                    const timelineSlider = document.getElementById('timeline');
                    
                    if (timelineData.timeSteps.length > 0) {{
                        noUiSlider.create(timelineSlider, {{
                            start: [0],
                            connect: 'lower',
                            step: 1,
                            range: {{
                                'min': 0,
                                'max': timelineData.timeSteps.length - 1
                            }},
                            format: {{
                                to: value => Math.round(value),
                                from: value => Math.round(value)
                            }}
                        }});
                        
                        // Update display when slider changes
                        timelineSlider.noUiSlider.on('update', function(values, handle) {{
                            const timeIndex = parseInt(values[handle]);
                            updateTimeDisplay(timeIndex);
                            updateSubmarinePositions(timeIndex);
                            simState.timeIndex = timeIndex;
                        }});
                    }}
                    
                    // Timeline control functions
                    function updateTimeDisplay(timeIndex) {{
                        const time = timelineData.timeSteps[timeIndex] || 0;
                        document.getElementById('current-time').textContent = `T+${{time}}h`;
                    }}
                    
                    function updateSubmarinePositions(timeIndex) {{
                        // Update submarine positions based on the time index
                        Object.entries(simState.submarinePositions).forEach(([id, subData]) => {{
                            // Find the position closest to this time index
                            let closestPosition = null;
                            let closestTimeDiff = Infinity;
                            
                            subData.positions.forEach(pos => {{
                                // Fix: Access coords instead of point
                                const timeDiff = Math.abs(pos.timeIndex - timeIndex);
                                if (timeDiff < closestTimeDiff) {{
                                    closestTimeDiff = timeDiff;
                                    closestPosition = pos.coords;
                                }}
                            }});
                            
                            // Update the marker position if we found a match
                            if (closestPosition) {{
                                submarineMarkers[id].setLatLng(closestPosition);
                            }}
                        }});
                        
                        // Update uncertainty visualization
                        updateUncertaintyDisplay(timeIndex);
                    }}
                    
                    function updateUncertaintyDisplay(timeIndex) {{
                        // Show/hide time step markers based on the current time
                        Object.entries(timeStepMarkers).forEach(([id, markers]) => {{
                            markers.forEach((marker, idx) => {{
                                if (idx <= timeIndex) {{
                                    if (!timeStepLayer.hasLayer(marker)) {{
                                        timeStepLayer.addLayer(marker);
                                    }}
                                }} else {{
                                    if (timeStepLayer.hasLayer(marker)) {{
                                        timeStepLayer.removeLayer(marker);
                                    }}
                                }}
                            }});
                        }});
                    }}
                    
                    // Play/pause the simulation
                    document.getElementById('play-pause').addEventListener('click', function() {{
                        if (simState.isPlaying) {{
                            // Pause
                            clearInterval(simState.playInterval);
                            this.innerHTML = '▶ Play';
                            simState.isPlaying = false;
                        }} else {{
                            // Play
                            this.innerHTML = '⏸ Pause';
                            simState.isPlaying = true;
                            
                            simState.playInterval = setInterval(() => {{
                                if (simState.timeIndex < simState.maxTimeIndex) {{
                                    simState.timeIndex++;
                                    timelineSlider.noUiSlider.set(simState.timeIndex);
                                }} else {{
                                    // End of simulation - stop playback
                                    clearInterval(simState.playInterval);
                                    document.getElementById('play-pause').innerHTML = '▶ Play';
                                    simState.isPlaying = false;
                                }}
                            }}, simState.speed);
                        }}
                    }});
                    
                    // Reset the simulation
                    document.getElementById('reset-time').addEventListener('click', function() {{
                        // Stop playback if running
                        if (simState.isPlaying) {{
                            clearInterval(simState.playInterval);
                            document.getElementById('play-pause').innerHTML = '▶ Play';
                            simState.isPlaying = false;
                        }}
                        
                        // Reset to beginning
                        simState.timeIndex = 0;
                        timelineSlider.noUiSlider.set(0);
                    }});
                }}

                // Control handlers with improved functionality
                const simulationsBtn = document.getElementById('toggle-simulations');
                simulationsBtn.addEventListener('click', () => {{
                    if (map.hasLayer(fcastLayer)) {{
                        map.removeLayer(fcastLayer);
                        simulationsBtn.textContent = "Show Simulations";
                        simulationsBtn.classList.remove('active');
                    }} else {{
                        map.addLayer(fcastLayer);
                        simulationsBtn.textContent = "Hide Simulations";
                        simulationsBtn.classList.add('active');
                    }}
                }});

                const historyBtn = document.getElementById('toggle-history');
                historyBtn.addEventListener('click', () => {{
                    if (map.hasLayer(histLayer)) {{
                        map.removeLayer(histLayer);
                        historyBtn.textContent = "Show History";
                        historyBtn.classList.remove('active');
                    }} else {{
                        map.addLayer(histLayer);
                        historyBtn.textContent = "Hide History";
                        historyBtn.classList.add('active');
                    }}
                }});
                
                const uncertaintyBtn = document.getElementById('toggle-uncertainty');
                uncertaintyBtn.addEventListener('click', () => {{
                    if (map.hasLayer(uncertaintyLayer) && map.hasLayer(timeStepLayer)) {{
                        map.removeLayer(uncertaintyLayer);
                        map.removeLayer(timeStepLayer);
                        uncertaintyBtn.textContent = "Show Uncertainty";
                        uncertaintyBtn.classList.remove('active');
                    }} else {{
                        map.addLayer(uncertaintyLayer);
                        map.addLayer(timeStepLayer);
                        uncertaintyBtn.textContent = "Hide Uncertainty";
                        uncertaintyBtn.classList.add('active');
                    }}
                }});

                document.getElementById('reset').addEventListener('click', () => {{
                    map.setView([21, 115], 5);
                }});

            }} catch (e) {{
                console.error('Error initializing map:', e);
                document.querySelector('.loading').textContent = 'Error loading map. Please check console for details.';
                document.querySelector('.loading').style.display = 'block'; // Make sure error is visible
            }}
        }});
    </script>
</body>
</html>
'''
    # Only keep the main output HTML file(s) in your output directory. Remove or ignore unused/old HTML files as needed.
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)