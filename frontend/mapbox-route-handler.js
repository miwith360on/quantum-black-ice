/**
 * Mapbox Integration for Black Ice Detection
 * Provides route optimization, hazard visualization, and safe route suggestions
 */

class MapboxRouteHandler {
    constructor(apiBaseUrl, mapboxToken) {
        this.apiBaseUrl = apiBaseUrl;
        this.mapboxToken = mapboxToken;
        this.map = null;
        this.routeLayers = [];
    }

    /**
     * Initialize Mapbox map
     */
    initializeMap(containerId) {
        if (!this.mapboxToken) {
            console.warn('⚠️ Mapbox token not configured');
            return false;
        }

        try {
            mapboxgl.accessToken = this.mapboxToken;
            this.map = new mapboxgl.Map({
                container: containerId,
                style: 'mapbox://styles/mapbox/streets-v12',
                center: [-83.0458, 42.3314], // Default to Michigan
                zoom: 10,
                pitch: 45,
                bearing: 0
            });

            // Add navigation controls
            this.map.addControl(new mapboxgl.NavigationControl());
            this.map.addControl(new mapboxgl.GeolocateControl({
                positionOptions: { enableHighAccuracy: true },
                trackUserLocation: true
            }));

            console.log('✅ Mapbox map initialized');
            return true;
        } catch (error) {
            console.error('❌ Mapbox initialization error:', error);
            return false;
        }
    }

    /**
     * Get optimized route with hazard analysis
     */
    async getOptimizedRoute(startLat, startLon, endLat, endLon) {
        try {
            const url = `${this.apiBaseUrl}/api/mapbox/directions` +
                `?start_lat=${startLat}&start_lon=${startLon}` +
                `&end_lat=${endLat}&end_lon=${endLon}` +
                `&mode=driving`;

            const response = await fetch(url);
            const data = await response.json();

            if (data.success && data.routes) {
                return data.routes;
            } else {
                console.error('Route error:', data.error);
                return [];
            }
        } catch (error) {
            console.error('❌ Route fetch error:', error);
            return [];
        }
    }

    /**
     * Display routes on map with color coding by hazard level
     */
    displayRoutes(routes) {
        if (!this.map) return;

        // Remove previous routes
        this.routeLayers.forEach(layerId => {
            if (this.map.getLayer(layerId)) {
                this.map.removeLayer(layerId);
            }
        });
        this.routeLayers = [];

        routes.forEach((route, index) => {
            const layerId = `route-${index}`;
            const hazardScore = route.hazard_score || 0.5;

            // Color code: green (safe) -> yellow (moderate) -> red (hazard)
            let color;
            if (hazardScore < 0.3) color = '#00FF00'; // Green
            else if (hazardScore < 0.6) color = '#FFFF00'; // Yellow
            else color = '#FF0000'; // Red

            // Add route line
            this.map.addSource(`route-source-${index}`, {
                type: 'geojson',
                data: {
                    type: 'Feature',
                    geometry: route.geometry
                }
            });

            this.map.addLayer({
                id: layerId,
                type: 'line',
                source: `route-source-${index}`,
                layout: {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                paint: {
                    'line-color': color,
                    'line-width': index === 0 ? 5 : 3, // Highlight safest route
                    'line-opacity': 0.8
                }
            });

            this.routeLayers.push(layerId);

            // Add popup on hover
            this.map.on('mouseenter', layerId, () => {
                this.map.getCanvas().style.cursor = 'pointer';
                const popup = new mapboxgl.Popup()
                    .setHTML(`
                        <div style="padding: 10px;">
                            <strong>${route.recommendation}</strong><br/>
                            Distance: ${(route.distance || 0).toFixed(1)} km<br/>
                            Duration: ${(route.duration || 0).toFixed(0)} min<br/>
                            Hazard: ${(route.hazard_score * 100).toFixed(0)}%<br/>
                            Risk: <span style="color: ${route.risk_level === 'high' ? 'red' : route.risk_level === 'moderate' ? 'orange' : 'green'}">
                                ${route.risk_level.toUpperCase()}
                            </span>
                        </div>
                    `)
                    .addTo(this.map);
            });

            this.map.on('mouseleave', layerId, () => {
                this.map.getCanvas().style.cursor = '';
            });
        });
    }

    /**
     * Add hazard layer to map (shows dangerous areas)
     */
    async showHazardLayer(hazardZones) {
        if (!this.map) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/mapbox/hazard-layer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hazard_zones: hazardZones })
            });

            const data = await response.json();

            if (data.success && data.geojson) {
                // Add hazard source and layer
                this.map.addSource('hazards', {
                    type: 'geojson',
                    data: data.geojson
                });

                this.map.addLayer({
                    id: 'hazard-points',
                    type: 'circle',
                    source: 'hazards',
                    paint: {
                        'circle-radius': 8,
                        'circle-color': '#FF0000',
                        'circle-opacity': 0.7,
                        'circle-stroke-width': 2,
                        'circle-stroke-color': '#FFF'
                    }
                });

                console.log('✅ Hazard layer added');
            }
        } catch (error) {
            console.error('❌ Hazard layer error:', error);
        }
    }

    /**
     * Show safe driving zone (isochrone)
     */
    async showSafeZone(lat, lon, minutes = 30) {
        if (!this.map) return;

        try {
            const response = await fetch(
                `${this.apiBaseUrl}/api/mapbox/safe-zone?lat=${lat}&lon=${lon}&minutes=${minutes}`
            );

            const data = await response.json();

            if (data.success && data.isochrone) {
                this.map.addSource('safe-zone', {
                    type: 'geojson',
                    data: data.isochrone
                });

                this.map.addLayer({
                    id: 'safe-zone-fill',
                    type: 'fill',
                    source: 'safe-zone',
                    paint: {
                        'fill-color': '#00FF00',
                        'fill-opacity': 0.2
                    }
                });

                this.map.addLayer({
                    id: 'safe-zone-border',
                    type: 'line',
                    source: 'safe-zone',
                    paint: {
                        'line-color': '#00FF00',
                        'line-width': 2
                    }
                });

                console.log(`✅ Safe zone (${minutes}min) shown`);
            }
        } catch (error) {
            console.error('❌ Safe zone error:', error);
        }
    }

    /**
     * Add marker to map
     */
    addMarker(lat, lon, title = '', color = 'blue') {
        if (!this.map) return;

        new mapboxgl.Marker({ color: color })
            .setLngLat([lon, lat])
            .setPopup(new mapboxgl.Popup().setHTML(`<div><strong>${title}</strong></div>`))
            .addTo(this.map);
    }

    /**
     * Fit map to bounds
     */
    fitBounds(routes) {
        if (!this.map || !routes.length) return;

        const bounds = new mapboxgl.LngLatBounds();
        
        routes.forEach(route => {
            if (route.geometry && route.geometry.coordinates) {
                route.geometry.coordinates.forEach(([lon, lat]) => {
                    bounds.extend([lon, lat]);
                });
            }
        });

        this.map.fitBounds(bounds, { padding: 50 });
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MapboxRouteHandler;
}
