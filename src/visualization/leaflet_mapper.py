"""Create Leaflet map visualizations for submarine tracking."""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from src.models.prediction import monte_carlo_simulation

logger = logging.getLogger(__name__)

def create_leaflet_map(data, output_path):
    """Create a Leaflet map visualization from submarine tracking data."""
    # Create dictionary to store submarine data
    submarine_forecasts = {}
    
    # Group data by submarine ID
    if isinstance(data, pd.DataFrame):
        grouped = data.groupby('sub_id')
        
        for sub_id, group in grouped:
            # Convert to records for Monte Carlo simulation
            records = group.to_dict('records')
            
            try:
                # Generate forecasts using Monte Carlo
                forecast = monte_carlo_simulation(
                    history=records,
                    num_simulations=500,
                    hours_ahead=48,
                    step_hours=3
                )
                
                # Add history path to forecast
                history_path = []
                for record in records:
                    history_path.append([float(record['longitude']), float(record['latitude'])])
                
                forecast['history_path'] = history_path
                forecast['forecast_path'] = []  # Simplified for now
                
                submarine_forecasts[sub_id] = forecast
                
            except Exception as e:
                logger.error(f"Error generating forecast for {sub_id}: {e}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # If this is a standalone HTML generation, use the template
    if str(output_path).endswith('.html'):
        html_template = Path(__file__).parent / 'map_template.html'
        
        # If template doesn't exist, copy the one you provided
        if not html_template.exists():
            with open(str(output_path), 'w') as f:
                f.write(get_html_template())
                
        # Replace the placeholder with actual data
        with open(str(output_path), 'w') as f:
            template = get_html_template()
            data_json = json.dumps(submarine_forecasts, indent=2)
            html_content = template.replace(
                'window.submarineForecasts = {};', 
                f'window.submarineForecasts = {data_json};'
            )
            f.write(html_content)
    
    logger.info(f"Map created: {output_path}")
    return submarine_forecasts

def get_html_template():
    """Return HTML template for the map with true hurricane-style probability cones using simulated points."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jin-Class SSBN Tracker</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/@turf/turf@6.5.0/turf.min.js"></script>
    <script src="https://unpkg.com/@ansur/leaflet-pulse-icon@0.1.1/dist/L.Icon.Pulse.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <link rel="stylesheet" href="https://unpkg.com/@ansur/leaflet-pulse-icon@0.1.1/dist/L.Icon.Pulse.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.js"></script>
    <style>
        :root { --accent: #198754; }
        body, html { margin: 0; padding: 0; height: 100vh; width: 100vw; overflow: hidden; font-family: system-ui, sans-serif; }
        #map { position: absolute; top: 0; left: 0; right: 0; bottom: 0; height: 100%; width: 100%; }
        .controls { position: absolute; top: 10px; right: 10px; z-index: 1000; background: white; padding: 10px; 
            border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.3); max-width: 180px; font-size: 13px; }
        .controls h3 { margin-top: 0; margin-bottom: 5px; font-size: 14px; }
        .submarine-info { margin-bottom: 8px; font-size: 12px; }
        .naval-base { background-color: #ff5722; border-radius: 50%; width: 10px; height: 10px; 
            border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5); }
        button { padding: 4px 8px; margin: 3px 0; cursor: pointer; background: var(--accent); color: white; 
            border: none; border-radius: 4px; font-size: 11px; width: 100%; text-align: left; }
        button.active { background: #0d6efd; }
        .legend { position: absolute; bottom: 30px; left: 10px; z-index: 1000; background: white; 
            padding: 8px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.3); font-size: 11px; max-width: 150px; }
        .legend-item { display: flex; align-items: center; margin-bottom: 3px; }
        .legend-color { display: inline-block; width: 12px; height: 12px; margin-right: 6px; border-radius: 50%; }
        .loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
            background: white; padding: 15px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.3); z-index: 1000; }
        .historical-path { stroke-width: 4; opacity: 0.8; }
        .forecast-path { stroke-width: 3; stroke-dasharray: 10, 5; opacity: 0.7; }
        .hurricane-cone { fill-opacity: 0.18; stroke-width: 2; }
        #time-control { position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); width: 50%; 
            z-index: 1000; background: white; padding: 8px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.3); }
        #timeline { height: 10px; margin: 5px 0; }
        .time-display { text-align: center; font-size: 12px; margin-bottom: 3px; }
        .play-controls { display: flex; justify-content: center; gap: 5px; }
        .play-controls button { width: auto; margin: 0; padding: 3px 8px; font-size: 11px; }
        .noUi-connect { background: var(--accent); }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="controls">
        <h3>Jin-Class SSBN Fleet</h3>
        <div class="submarine-info">Tracking 6 Jin-Class (Type 094) Nuclear Submarines</div>
        <button id="toggle-simulations" class="active">Hide Simulations</button>
        <button id="toggle-history" class="active">Hide History</button>
        <button id="toggle-confidence" class="active">Hide Confidence</button>
        <button id="reset">Reset View</button>
    </div>
    <div class="legend">
        <div class="legend-item"><span class="legend-color" style="background-color: #ff5722;"></span><span>Naval Base</span></div>
        <div class="legend-item"><span class="legend-color" style="background-color: var(--accent);"></span><span>Current Position</span></div>
        <div class="legend-item"><span style="height: 3px; background-color: #0d6efd; width: 12px; display: inline-block;"></span><span>History</span></div>
        <div class="legend-item"><span style="height: 2px; border-top: 2px dashed #e91e63; width: 12px; display: inline-block;"></span><span>Forecast</span></div>
        <div class="legend-item"><span class="legend-color" style="background-color: rgba(25, 135, 84, 0.2);"></span><span>Hurricane Cone (90% Monte Carlo)</span></div>
    </div>
    <div id="time-control">
        <div class="time-display">Time: <span id="current-time">T+0h</span></div>
        <div id="timeline"></div>
        <div class="play-controls">
            <button id="play-pause">▶ Play</button>
            <button id="reset-time">Reset</button>
        </div>
    </div>
    <div class="loading">Loading map...</div>
    <script>
        window.addEventListener('load', function() {
            document.querySelector('.loading').style.display = 'none';
            window.submarineForecasts = {};
            
            // Naval bases and sea waypoints
            const navalBases = [
                { name: "Yulin Naval Base", coords: [18.229, 109.706] },
                { name: "Qingdao Base", coords: [36.071, 120.418] },
                { name: "Ningbo Base", coords: [29.868, 122.108] },
                { name: "Xiamen Base", coords: [24.455, 118.082] },
                { name: "Xiaopingdao Base", coords: [38.822, 121.536] }
            ];
            
            const seaWaypoints = [
                { name: "SCS1", coords: [16.0, 114.0] },
                { name: "SCS2", coords: [13.2, 117.4] }, 
                { name: "SCS3", coords: [20.5, 118.7] },
                { name: "ECS1", coords: [27.5, 123.6] },
                { name: "ECS2", coords: [31.3, 125.8] },
                { name: "YS1", coords: [35.6, 122.5] },
                { name: "TS1", coords: [23.2, 119.8] },
                { name: "PS1", coords: [22.0, 126.0] },
                { name: "PS2", coords: [18.0, 128.0] }
            ];

            try {
                // Initialize map
                const map = L.map('map', { minZoom: 3, detectRetina: true }).setView([21, 115], 5);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19, attribution: '© OpenStreetMap'
                }).addTo(map);

                // Create layer groups
                const histLayer = L.layerGroup().addTo(map);
                const fcastLayer = L.layerGroup().addTo(map);
                const confidenceLayer = L.layerGroup().addTo(map);
                const baseLayer = L.layerGroup().addTo(map);
                const posLayer = L.layerGroup().addTo(map);

                // Add naval bases
                navalBases.forEach(base => {
                    L.marker(base.coords, {
                        icon: L.divIcon({ className: 'naval-base', iconSize: [10, 10] })
                    })
                    .bindTooltip(base.name, { permanent: false })
                    .addTo(baseLayer);
                });
                
                // Initialize state and objects
                const simState = {
                    timeIndex: 0,
                    maxTimeIndex: 0,
                    isPlaying: false,
                    playInterval: null,
                    speed: 1000,
                    submarinePositions: {}
                };
                const submarineMarkers = {};
                const submarinePaths = {};
                const submarineHistoryPaths = {};
                const confidenceRings = {};

                // Find sea route avoiding land
                function findSeaRoute(start, end) {
                    const startPoint = [start[1], start[0]];
                    const endPoint = [end[1], end[0]];
                    const distance = turf.distance(
                        turf.point([start[0], start[1]]), 
                        turf.point([end[0], end[1]]), 
                        {units: 'kilometers'}
                    );
                    
                    if (distance < 300) return [startPoint, endPoint];
                    
                    let waypoints = [];
                    
                    // Choose appropriate waypoints based on location
                    if (start[1] < 25 && end[1] < 25) {
                        waypoints = [seaWaypoints[0], seaWaypoints[1]]; // South China Sea
                    } else if (start[1] > 30 && end[1] > 30) {
                        waypoints = [seaWaypoints[5]]; // Yellow Sea
                    } else {
                        waypoints = [seaWaypoints[3], seaWaypoints[4]]; // East China Sea
                    }
                    
                    const route = [startPoint];
                    waypoints.forEach(wp => route.push([wp.coords[0], wp.coords[1]]));
                    route.push(endPoint);
                    return route;
                }

                // Create hurricane-style confidence rings
                function createConfidenceRings(timeSteps, points, color, id) {
                    if (!timeSteps || timeSteps.length === 0 || !points || points.length === 0) return [];
                    
                    const layers = [];
                    const confidenceGroup = L.layerGroup();
                    
                    for (let i = 0; i < Math.min(timeSteps.length, points.length); i++) {
                        const center = [points[i][1], points[i][0]];
                        const timeStep = timeSteps[i];
                        
                        // Calculate uncertainty radius that grows with time
                        const innerRadius = 15 + (i * 10);
                        const outerRadius = innerRadius * 1.5;
                        
                        // 67% confidence ring (inner)
                        const innerConfidenceRing = L.circle(center, {
                            radius: innerRadius * 1000,
                            color: color,
                            weight: 2,
                            fillColor: color,
                            fillOpacity: 0.2,
                            className: 'confidence-ring-67'
                        }).bindTooltip(`T+${timeStep}h: 67% confidence`);
                        
                        // 90% confidence ring (outer)
                        const outerConfidenceRing = L.circle(center, {
                            radius: outerRadius * 1000,
                            color: color,
                            weight: 1,
                            fillColor: color,
                            fillOpacity: 0.1,
                            dashArray: '5,5',
                            className: 'confidence-ring-90'
                        }).bindTooltip(`T+${timeStep}h: 90% confidence`);
                        
                        // Label
                        const labelIcon = L.divIcon({
                            className: 'confidence-label',
                            html: `T+${timeStep}h`,
                            iconSize: [40, 16],
                            iconAnchor: [20, 8]
                        });
                        
                        const label = L.marker(center, { icon: labelIcon });
                        
                        // Add everything to the group
                        confidenceGroup.addLayer(innerConfidenceRing);
                        confidenceGroup.addLayer(outerConfidenceRing);
                        confidenceGroup.addLayer(label);
                        
                        layers.push({
                            timeStep: timeStep,
                            elements: [innerConfidenceRing, outerConfidenceRing, label]
                        });
                    }
                    
                    confidenceGroup.addTo(confidenceLayer);
                    return { group: confidenceGroup, layers: layers };
                }

                // Initialize timeline data
                let timelineData = { minTime: 0, maxTime: 0, timeSteps: [] };

                if (Object.keys(window.submarineForecasts).length === 0) {
                    // No subs - show message and hide timeline
                    document.body.appendChild(
                        Object.assign(document.createElement('div'), {
                            style: 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(255,255,255,0.95);padding:2em 3em;border-radius:10px;box-shadow:0 0 10px rgba(0,0,0,0.2);font-size:1.3em;',
                            innerText: 'No submarine forecast data available.'
                        })
                    );
                    document.getElementById('time-control').style.display = 'none';
                } else {
                    // Submarine colors
                    const submarineColors = ['#0d6efd', '#e91e63', '#9c27b0', '#ff9800', '#8bc34a', '#795548'];
                    
                    // Collect all time steps from forecasts
                    Object.values(window.submarineForecasts).forEach(data => {
                        if (data.forecast_times?.length) {
                            data.forecast_times.forEach(time => {
                                if (!timelineData.timeSteps.includes(time)) timelineData.timeSteps.push(time);
                            });
                        }
                    });
                    
                    // Sort time steps and set limits
                    timelineData.timeSteps.sort((a, b) => a - b);
                    timelineData.minTime = timelineData.timeSteps[0] || 0;
                    timelineData.maxTime = timelineData.timeSteps[timelineData.timeSteps.length - 1] || 0;
                    simState.maxTimeIndex = timelineData.timeSteps.length - 1;
                    
                    // Process each submarine
                    Object.entries(window.submarineForecasts).forEach(([id, data], idx) => {
                        try {
                            const color = submarineColors[idx % submarineColors.length];
                            
                            // Create submarine marker
                            const lastPos = data.central_path[data.central_path.length - 1];
                            const marker = L.marker([lastPos[1], lastPos[0]], {
                                icon: L.icon.pulse({
                                    iconSize: [14, 14],
                                    color: color,
                                    fillColor: color,
                                    animate: true
                                })
                            }).addTo(posLayer)
                            .bindPopup(`<strong>Jin${idx+1}</strong><br>Position: ${lastPos[1].toFixed(4)}, ${lastPos[0].toFixed(4)}`);
                            
                            submarineMarkers[id] = marker;
                            simState.submarinePositions[id] = { color, positions: [], marker };

                            // Draw historical path
                            if (data.history_path?.length > 1) {
                                let seaRoutedPath = [];
                                for (let i = 0; i < data.history_path.length - 1; i++) {
                                    seaRoutedPath = seaRoutedPath.concat(
                                        findSeaRoute(data.history_path[i], data.history_path[i+1])
                                    );
                                }
                                
                                submarineHistoryPaths[id] = L.polyline(seaRoutedPath, {
                                    color: color,
                                    weight: 4,
                                    opacity: 0.8,
                                    className: 'historical-path',
                                    smoothFactor: 1
                                }).addTo(histLayer);
                            }

                            // Draw forecast path
                            if (data.forecast_path?.length > 0) {
                                let startPoint = data.history_path?.length ? 
                                    data.history_path[data.history_path.length-1] : 
                                    data.central_path[data.central_path.length-1];
                                
                                let seaRoutedForecast = [];
                                let lastPoint = startPoint;
                                
                                data.forecast_path.forEach((forecastPoint, idx) => {
                                    seaRoutedForecast = seaRoutedForecast.concat(
                                        findSeaRoute(lastPoint, forecastPoint)
                                    );
                                    lastPoint = forecastPoint;
                                    
                                    const timeIndex = idx < data.forecast_times.length ? idx : 0;
                                    simState.submarinePositions[id].positions.push({
                                        coords: [forecastPoint[1], forecastPoint[0]],
                                        timeIndex: timeIndex
                                    });
                                });
                                
                                submarinePaths[id] = L.polyline(seaRoutedForecast, {
                                    color: color,
                                    weight: 3,
                                    dashArray: '10, 5',
                                    opacity: 0.7,
                                    className: 'forecast-path',
                                    smoothFactor: 1
                                }).addTo(fcastLayer);
                            }
                            
                            // Create confidence rings
                            if (data.confidence_rings?.length > 0) {
                                confidenceRings[id] = createConfidenceRings(
                                    data.forecast_times,
                                    data.forecast_path,
                                    color,
                                    id
                                );
                            }

                            // After drawing confidence rings, add:
                            if (data.simulated_points?.length > 1) {
                                const cone = drawMonteCarloCone(data.simulated_points, color);
                                if (cone) cone.addTo(confidenceLayer);
                            }
                        } catch (e) {
                            console.error(`Error processing submarine ${id}:`, e);
                        }
                    });
                    
                    // Initialize timeline slider
                    const timelineSlider = document.getElementById('timeline');
                    
                    if (timelineData.timeSteps.length > 0) {
                        noUiSlider.create(timelineSlider, {
                            start: [0],
                            connect: 'lower',
                            step: 1,
                            range: { 'min': 0, 'max': timelineData.timeSteps.length - 1 },
                            format: { to: v => Math.round(v), from: v => Math.round(v) }
                        });
                        
                        timelineSlider.noUiSlider.on('update', function(values) {
                            const timeIndex = parseInt(values[0]);
                            
                            // Update display and state
                            const time = timelineData.timeSteps[timeIndex] || 0;
                            document.getElementById('current-time').textContent = `T+${time}h`;
                            simState.timeIndex = timeIndex;
                            
                            // Update submarine positions
                            Object.entries(simState.submarinePositions).forEach(([id, subData]) => {
                                let closestPosition = null;
                                let closestTimeDiff = Infinity;
                                
                                subData.positions.forEach(pos => {
                                    const timeDiff = Math.abs(pos.timeIndex - timeIndex);
                                    if (timeDiff < closestTimeDiff) {
                                        closestTimeDiff = timeDiff;
                                        closestPosition = pos.coords;
                                    }
                                });
                                
                                if (closestPosition) submarineMarkers[id].setLatLng(closestPosition);
                            });
                            
                            // Update confidence ring visibility
                            Object.values(confidenceRings).forEach(ringSet => {
                                if (ringSet?.layers) {
                                    ringSet.layers.forEach(layer => {
                                        const layerIndex = timelineData.timeSteps.indexOf(layer.timeStep);
                                        
                                        layer.elements.forEach(element => {
                                            if (layerIndex <= timeIndex) {
                                                if (!confidenceLayer.hasLayer(element)) 
                                                    confidenceLayer.addLayer(element);
                                            } else {
                                                if (confidenceLayer.hasLayer(element)) 
                                                    confidenceLayer.removeLayer(element);
                                            }
                                        });
                                    });
                                }
                            });
                        });
                    }
                    
                    // Play/pause button
                    document.getElementById('play-pause').addEventListener('click', function() {
                        if (simState.isPlaying) {
                            clearInterval(simState.playInterval);
                            this.innerHTML = '▶ Play';
                            simState.isPlaying = false;
                        } else {
                            this.innerHTML = '⏸ Pause';
                            simState.isPlaying = true;
                            
                            simState.playInterval = setInterval(() => {
                                if (simState.timeIndex < simState.maxTimeIndex) {
                                    simState.timeIndex++;
                                    timelineSlider.noUiSlider.set(simState.timeIndex);
                                } else {
                                    clearInterval(simState.playInterval);
                                    document.getElementById('play-pause').innerHTML = '▶ Play';
                                    simState.isPlaying = false;
                                }
                            }, simState.speed);
                        }
                    });
                    
                    // Reset button
                    document.getElementById('reset-time').addEventListener('click', function() {
                        if (simState.isPlaying) {
                            clearInterval(simState.playInterval);
                            document.getElementById('play-pause').innerHTML = '▶ Play';
                            simState.isPlaying = false;
                        }
                        simState.timeIndex = 0;
                        timelineSlider.noUiSlider.set(0);
                    });
                }

                // Toggle buttons
                document.getElementById('toggle-simulations').addEventListener('click', function() {
                    if (map.hasLayer(fcastLayer)) {
                        map.removeLayer(fcastLayer);
                        this.textContent = "Show Simulations";
                        this.classList.remove('active');
                    } else {
                        map.addLayer(fcastLayer);
                        this.textContent = "Hide Simulations";
                        this.classList.add('active');
                    }
                });

                document.getElementById('toggle-history').addEventListener('click', function() {
                    if (map.hasLayer(histLayer)) {
                        map.removeLayer(histLayer);
                        this.textContent = "Show History";
                        this.classList.remove('active');
                    } else {
                        map.addLayer(histLayer);
                        this.textContent = "Hide History";
                        this.classList.add('active');
                    }
                });
                
                document.getElementById('toggle-confidence').addEventListener('click', function() {
                    if (map.hasLayer(confidenceLayer)) {
                        map.removeLayer(confidenceLayer);
                        this.textContent = "Show Confidence";
                        this.classList.remove('active');
                    } else {
                        map.addLayer(confidenceLayer);
                        this.textContent = "Hide Confidence";
                        this.classList.add('active');
                    }
                });

                document.getElementById('reset').addEventListener('click', () => 
                    map.setView([21, 115], 5)
                );

                // Add this function to draw the hurricane cone using simulated points
                function drawMonteCarloCone(simulatedPoints, color) {
                    if (!simulatedPoints || simulatedPoints.length < 2) return null;
                    let conePoints = [];
                    // For each forecast step, get the convex hull of the outermost 90% of simulated points
                    for (let i = 0; i < simulatedPoints.length; i++) {
                        let points = simulatedPoints[i];
                        if (!points || points.length < 3) continue;
                        // Convert to GeoJSON points
                        let features = points.map(pt => turf.point([pt[0], pt[1]]));
                        let fc = turf.featureCollection(features);
                        // Compute convex hull
                        let hull = turf.convex(fc);
                        if (hull && hull.geometry && hull.geometry.coordinates.length > 0) {
                            // Use the first ring of the hull
                            let ring = hull.geometry.coordinates[0];
                            // Add points in order for the forward pass
                            conePoints = conePoints.concat(ring);
                        }
                    }
                    // Optionally, close the polygon by adding the first point again
                    if (conePoints.length > 0) {
                        conePoints.push(conePoints[0]);
                        return L.polygon(conePoints.map(pt => [pt[1], pt[0]]), {
                            color: color,
                            fillColor: color,
                            fillOpacity: 0.18,
                            weight: 2,
                            className: 'hurricane-cone'
                        });
                    }
                    return null;
                }

            } catch (e) {
                console.error('Error initializing map:', e);
                document.querySelector('.loading').textContent = 'Error loading map';
                document.querySelector('.loading').style.display = 'block';
            }
        });
    </script>
</body>
</html>
"""