import json
import os
import random
import math

def create_leaflet_map(forecasts, output_path):
    """
    Write a Leaflet+D3 HTML visualization for submarine forecasts with Monte-Carlo simulation.
    Embeds the forecast data as a JS variable in the HTML.
    """
    forecast_json = json.dumps(forecasts, indent=2)
    
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jin-Class SSBN Monte-Carlo Tracker</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <style>
        :root {{ --accent: #198754; /* green */ }}
        body, html {{ margin: 0; height: 100%; font-family: system-ui, sans-serif; }}
        #map {{ height: 100%; }}
        .controls {{ 
            position: absolute; 
            top: 20px; 
            right: 20px; 
            z-index: 1000; 
            background: white; 
            padding: 10px; 
            border-radius: 5px; 
            box-shadow: 0 0 10px rgba(0,0,0,0.3); 
        }}
        .submarine-marker {{
            background: var(--accent);
            width: 22px;
            height: 22px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font: 600 0.7rem/1 system-ui;
        }}
        .source-point {{
            background-color: var(--accent);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            text-align: center;
            line-height: 30px;
            color: white;
            font-weight: bold;
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
            padding: 5px 10px; 
            margin: 5px; 
            cursor: pointer; 
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 3px;
        }}
        .legend {{ 
            position: absolute; 
            bottom: 30px; 
            left: 10px; 
            z-index: 1000; 
            background: white; 
            padding: 10px; 
            border-radius: 5px; 
            box-shadow: 0 0 10px rgba(0,0,0,0.3); 
            font-size: 12px; 
        }}
        .legend-item {{ 
            display: flex; 
            align-items: center; 
            margin-bottom: 5px; 
        }}
        .legend-color {{ 
            display: inline-block; 
            width: 15px; 
            height: 15px; 
            margin-right: 5px; 
            border-radius: 50%; 
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="controls">
        <h3>Jin-Class SSBN Fleet Control</h3>
        <div class="submarine-info">
            Tracking {{num_subs}} Jin-Class (Type 094) Nuclear Submarines
        </div>
        <button id="toggle-simulations">Toggle Simulations</button>
        <button id="toggle-rings">Toggle Uncertainty Rings</button>
        <button id="reset">Reset View</button>
    </div>
    <div class="legend">
        <div class="legend-item">
            <span class="legend-color" style="background-color: var(--accent);"></span>
            <span>Submarine Position</span>
        </div>
        <div class="legend-item">
            <span style="border: 2px dashed var(--accent); width: 15px; display: inline-block;"></span>
            <span>Mean Trajectory</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: rgba(25, 135, 84, 0.2);"></span>
            <span>Uncertainty Range</span>
        </div>
    </div>
    <script>
        // Submarine forecast data from Python
        window.submarineForecasts = {forecast_json};

        // Initialize map with retina support
        const map = L.map('map', {{ minZoom: 3, detectRetina: true }}).setView([18, 115], 6);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }}).addTo(map);

        // Create markers and visualizations
        const submarineMarkers = {{}};
        const submarinePaths = {{}};
        const uncertaintyRings = {{}};
        const uncertaintyCones = {{}};

        Object.entries(window.submarineForecasts).forEach(([id, data], idx) => {{
            const color = d3.schemeCategory10[idx % 10];
            
            // Create submarine marker at last known position
            const lastPos = data.central_path[data.central_path.length - 1];
            const marker = L.marker([lastPos[1], lastPos[0]], {{
                icon: L.divIcon({{
                    className: 'submarine-marker',
                    html: `<div style="background-color:${{color}}">${{idx + 1}}</div>`,
                    iconSize: [22, 22]
                }})
            }}).addTo(map)
            .bindPopup(`<b>${{id}}</b><br>Position: ${{lastPos[1].toFixed(2)}}°N ${{lastPos[0].toFixed(2)}}°E`);

            submarineMarkers[id] = marker;

            // Create mean trajectory path
            const path = L.polyline(data.central_path.map(p => [p[1], p[0]]), {{
                color: color,
                weight: 2,
                dashArray: '6,4'
            }}).addTo(map);
            submarinePaths[id] = path;

            // Create uncertainty cone
            const cone = L.polygon(data.cone_polygon.map(p => [p[1], p[0]]), {{
                color: color,
                weight: 1,
                fillColor: color,
                fillOpacity: 0.2
            }}).addTo(map);
            uncertaintyCones[id] = cone;

            // Create uncertainty rings
            const rings = [];
            data.central_path.slice(1).forEach((p, idx) => {{
                const base = 2000 + idx * 1000; // metres
                for (let r = 0; r < 3; r++) {{
                    const ring = L.circle([p[1], p[0]], {{
                        radius: base + r * 1000,
                        stroke: true,
                        color: color,
                        weight: 1,
                        fill: false,
                        opacity: 0.5 - r * 0.1
                    }}).addTo(map);
                    rings.push(ring);
                }}
            }});
            uncertaintyRings[id] = rings;
        }});

        // Control handlers
        document.getElementById('toggle-simulations').addEventListener('click', () => {{
            Object.values(submarinePaths).forEach(path => {{
                if (map.hasLayer(path)) map.removeLayer(path);
                else map.addLayer(path);
            }});
            Object.values(uncertaintyCones).forEach(cone => {{
                if (map.hasLayer(cone)) map.removeLayer(cone);
                else map.addLayer(cone);
            }});
        }});

        document.getElementById('toggle-rings').addEventListener('click', () => {{
            Object.values(uncertaintyRings).forEach(rings => {{
                rings.forEach(ring => {{
                    if (map.hasLayer(ring)) map.removeLayer(ring);
                    else map.addLayer(ring);
                }});
            }});
        }});

        document.getElementById('reset').addEventListener('click', () => {{
            map.setView([18, 115], 6);
        }});
    </script>
</body>
</html>
'''
    html_template = html_template.replace("{{num_subs}}", str(len(forecasts)))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template) 