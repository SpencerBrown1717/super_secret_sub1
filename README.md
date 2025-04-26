## 🎯 Mission Objectives

- Track 6 Chinese nuclear-powered submarines
- Monitor 1 Russian-supported Chinese submarine
- Predict future positions using reinforcement learning

# Python Codebase for Tracking and Forecasting Jin-Class Submarine Movements

## Introduction  
China's **Type 094 Jin-class** submarines are nuclear-powered ballistic missile submarines (SSBNs) that form the backbone of China's sea-based nuclear deterrent. The People's Liberation Army Navy (PLAN) currently operates six Jin-class SSBNs, each capable of carrying JL-2 or JL-3 submarine-launched ballistic missiles. These submarines are of high strategic importance and are nicknamed part of the "Silent Service" due to their ability to hide underwater for extended periods. Tracking their movements is a complex task, but advances in open-source intelligence (e.g. satellite imagery) have made it possible to observe when these subs leave or enter ports.

This project outlines a **Python-based codebase** to track the six Jin-class SSBNs, ingest sightings/departure data, predict their possible future tracks (similar to hurricane forecast cones of uncertainty), and visualize these tracks on a map. The design emphasizes modularity and clarity so that new data sources or visualization tools (like deck.gl) can be integrated easily in the future. We focus **only on Jin-class nuclear missile submarines** – no diesel-electric subs or other classes – to tailor the solution to their specific operational patterns and significance.

**Key Features and Goals:**  
- **Data Ingestion:** Accept data on submarine sightings or departures from CSV files and/or API endpoints, and normalize this input for processing.  
- **Tracking Module:** Maintain up-to-date information on each of the six Jin-class subs (identity, last known position/time, status).  
- **Prediction Module:** Forecast each submarine's future movement, generating a probable path and an **uncertainty cone** around that path, analogous to hurricane trajectory forecasts.  
- **Visualization:** Provide a basic map visualization of the predicted tracks and uncertainty regions using Python (with the flexibility to swap in advanced tools like deck.gl later).  
- **Modularity & Extensibility:** Structure the code into clear modules (ingestion, prediction, visualization, etc.) with clean interfaces and comments, so that others can easily add new data or extend functionality over time.  
- **Hackathon-Ready:** Keep the implementation simple and well-documented, favoring readability and quick iteration. For now, use simulated or static data if live data isn't available, but ensure the pipeline can integrate real feeds when ready.

## Data Ingestion Module (CSV/API Inputs)  
The **data ingestion module** handles incoming information about submarine movements. This data might come as: (a) CSV files containing timestamped sightings/locations, or (b) API endpoints that provide real-time updates in JSON/XML format. The module will parse these inputs and output a standardized data structure (e.g. a Python list of dicts or a Pandas DataFrame) for use by other components.

**Key tasks of the ingestion module:**  
- Read data from multiple sources (files or web endpoints).  
- Parse and validate fields (e.g. submarine identifier, type, latitude, longitude, timestamp, and event type like "departure", "sighting", "arrival").  
- Filter data to include only Type 094 Jin-class submarines. We can maintain a list of the six Jin-class sub IDs (e.g., hull numbers or names) and ignore records about other vessels. This ensures we **focus only on Jin-class SSBNs** as required.  
- Handle incremental updates: new data can be ingested periodically (e.g., on a schedule or when a new CSV is dropped in). The code should be able to append new records to the existing dataset and sort or index by time.

## Submarine Tracking Data Model  
After ingestion, we need to maintain the state of each submarine. A simple approach is to use a **dictionary or a class object** for each submarine. For example, we might define a class `Submarine` with attributes like `name`, `last_known_position`, `last_known_time`, and `history` (list of past sightings). However, for a quick implementation, a Python dict for each sub (or a DataFrame grouped by sub) can suffice.

**State tracking for each sub might include:**  
- **Identity:** Submarine name or ID (e.g., `"Jin 1"` through `"Jin 6"`).  
- **Last known latitude/longitude:** from the most recent sighting or report.  
- **Last known timestamp:** when that position was valid.  
- **Current status:** possibly whether at sea or in port (if such info can be deduced from data). For instance, a "departure" event from the home base might mark it as "at sea".  
- **History of positions:** a list or DataFrame of past locations and times, which could be useful for analyzing speed and heading.  

## Prediction Module (Movement Forecast with Uncertainty)  
The **prediction module** takes the current state of a submarine and projects its future positions, much like meteorologists project a hurricane's path. Because submarines are stealthy and can choose their course, predicting their track is inherently uncertain – hence the need to generate a **"cone of uncertainty"** around the forecast.

**Approach to predicting submarine movement:**  
1. **Initial State:** Use the last known position and time for the sub. If we have an estimate of its heading (direction) and speed from the data (for example, if multiple sightings indicate a course), use that. If not, we may assume a nominal heading (or consider multiple possible directions). For Jin-class subs, if they just departed their base, a reasonable assumption is they head to deep water in the South China Sea or nearby Pacific areas for patrol.  
2. **Movement Model:** For simplicity, we can model the submarine's movement with basic kinematics:
   - Assume a speed (e.g. 5–10 knots while on patrol, which is roughly 9–18 km/h). Jin-class SSBNs likely travel at **low speeds to remain quiet** during patrol.
   - Assume a course (bearing). If unknown, we might run the prediction for several different bearings (e.g., spreading out like a fan). If a prior heading can be inferred from two consecutive sightings, use that as the base course.
   - Account for constraints: the sub will remain underwater and likely avoid shallow areas or straits where detection is easier. If we have a map of water depth or known patrol zones, we could bias the path toward those areas.  
3. **Time Steps:** Generate forecast positions at regular intervals (say every 6 or 12 hours) for a certain horizon (e.g., 5 days into the future, similar to hurricane forecasts). Each step, update position based on speed and heading. We might add random minor deviations to simulate the sub not holding a perfectly straight line.  

## Visualization Module (Map and Cone Display)  
The visualization module generates a **map** showing the submarine tracks and their forecast cones. At this stage, we aim for a basic but functional visualization using Python tools. In future, the visualization can be swapped out or augmented with web-based libraries like **deck.gl** or Mapbox for richer interactivity, but the current goal is to produce a quick visual output for analysis.

**What to visualize:**  
- The **last known location** of each Jin-class sub (mark it on the map, perhaps with a distinct icon or color per sub).  
- The **predicted path** (center of the cone) for each sub that is currently at sea. If a sub is in port (no departure event yet), we might not draw a path. The path can be drawn as a polyline connecting the forecast points.  
- The **uncertainty cone/area** for each forecast. With Folium, we can draw circles at each forecast position with the computed radius. These circles (when semi-transparent and overlapping) will visually approximate a cone of uncertainty.  

## Pipeline Architecture and Module Integration  
With ingestion, tracking, prediction, and visualization components outlined, we can design the overall pipeline. The system can be organized in a few Python modules (files), for example:  

- `ingestion.py` – functions to load/fetch data from CSV or API, and filter for Jin-class subs.  
- `models.py` (or `prediction.py`) – functions or classes for predicting submarine movement and calculating uncertainty.  
- `visualize.py` – functions for plotting the data on a map (initially using Folium).  
- `main.py` – orchestrator script that ties everything together: it calls the ingestion to get data, updates the tracking state, runs predictions for each sub, and then calls visualization to output the map.  

## Extensibility and Future Integration (deck.gl, etc.)  
We have kept the design flexible for future extensions:  

- **Adding New Data:** If more data sources come online (e.g., crowd-sourced sighting reports, sonar data, etc.), one can integrate them by adding new ingestion functions.  
- **Additional Submarines or Vessel Types:** While the current focus is strictly on the six Jin-class SSBNs, the system could be generalized.  
- **Visualization Upgrades:** The map output is intentionally basic. In a full application, we might use a web framework or interactive dashboard. Tools like **deck.gl** (via its Python binding **pydeck**) allow high-performance rendering of many objects on a map.  
- **Real-Time Operation:** The architecture could support a loop or scheduled job where new data is ingested periodically and the predictions/visualization are updated.  

## Conclusion  
This Python codebase provides a **comprehensive pipeline** for tracking six Jin-class submarines and forecasting their future locations with an uncertainty cone akin to hurricane path forecasts. We ingest data flexibly from CSV files or APIs, maintain a clear state for each submarine, and use a simple predictive model to generate possible future tracks. The output is visualized on a map for easy interpretation. Throughout the code, we emphasize clarity (with comments and logical structure) so that it's easy for others to understand and extend. The current visualization is kept basic for immediate results, but the modular design ensures we can later integrate advanced mapping libraries like deck.gl or connect the pipeline to a live dashboard without overhauling the core logic.