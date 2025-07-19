/**
 * AVA OLO Field Drawing Library
 * Shared field drawing functionality for all dashboards
 * Constitutional compliant - works for Bulgarian mango farmers
 */

// Global variables
let fieldMap = null;
let fieldDrawingManager = null;
let currentFieldPolygon = null;
let fieldMarkers = [];
let isFieldDrawing = false;

// Initialize map (called by Google Maps API)
function initMap() {
    const mapOptions = {
        center: { lat: 42.7339, lng: 25.4858 }, // Center of Bulgaria
        zoom: 7,
        mapTypeId: 'satellite',
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
            position: google.maps.ControlPosition.TOP_RIGHT
        },
        streetViewControl: false,
        fullscreenControl: true,
        mapId: 'e2a6d55c7b7beb3685a30de3' // Required Map ID
    };
    
    fieldMap = new google.maps.Map(document.getElementById('field-map'), mapOptions);
    
    // Initialize drawing manager
    fieldDrawingManager = new google.maps.drawing.DrawingManager({
        drawingMode: null,
        drawingControl: false,
        polygonOptions: {
            fillColor: '#228B22',
            fillOpacity: 0.35,
            strokeWeight: 2,
            strokeColor: '#006400',
            clickable: true,
            editable: true,
            draggable: false
        }
    });
    
    fieldDrawingManager.setMap(fieldMap);
    
    // Handle polygon completion
    google.maps.event.addListener(fieldDrawingManager, 'polygoncomplete', function(polygon) {
        handlePolygonComplete(polygon);
    });
    
    // Try to get user's location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            fieldMap.setCenter(userLocation);
            fieldMap.setZoom(14);
        }, function() {
            console.log('Geolocation failed or was denied');
        });
    }
}

// Start drawing a field
window.startFieldDrawing = function() {
    if (!fieldDrawingManager) {
        console.error('Drawing manager not initialized');
        return;
    }
    
    // Clear any existing polygon
    clearFieldDrawing();
    
    // Enable polygon drawing mode
    fieldDrawingManager.setDrawingMode(google.maps.drawing.OverlayType.POLYGON);
    isFieldDrawing = true;
};

// Clear field drawing
window.clearFieldDrawing = function() {
    // Remove current polygon
    if (currentFieldPolygon) {
        currentFieldPolygon.setMap(null);
        currentFieldPolygon = null;
    }
    
    // Clear markers
    fieldMarkers.forEach(marker => marker.setMap(null));
    fieldMarkers = [];
    
    // Reset drawing mode
    if (fieldDrawingManager) {
        fieldDrawingManager.setDrawingMode(null);
    }
    
    isFieldDrawing = false;
};

// Handle polygon completion
function handlePolygonComplete(polygon) {
    // Store the polygon
    currentFieldPolygon = polygon;
    
    // Disable drawing mode
    fieldDrawingManager.setDrawingMode(null);
    
    // Calculate area and center
    const area = calculatePolygonArea(polygon);
    const centroid = calculatePolygonCentroid(polygon);
    const vertices = polygon.getPath();
    const pointCount = vertices.getLength();
    
    // Convert area from square meters to hectares
    const areaInHectares = area / 10000;
    
    // Call callback if defined
    if (window.onFieldPolygonComplete) {
        window.onFieldPolygonComplete(areaInHectares, centroid, pointCount);
    }
    
    // Allow editing
    polygon.setEditable(true);
    
    // Update calculations when polygon is edited
    google.maps.event.addListener(polygon.getPath(), 'set_at', function() {
        updatePolygonCalculations(polygon);
    });
    
    google.maps.event.addListener(polygon.getPath(), 'insert_at', function() {
        updatePolygonCalculations(polygon);
    });
    
    google.maps.event.addListener(polygon.getPath(), 'remove_at', function() {
        updatePolygonCalculations(polygon);
    });
}

// Calculate polygon area using Google Maps geometry library
function calculatePolygonArea(polygon) {
    return google.maps.geometry.spherical.computeArea(polygon.getPath());
}

// Calculate polygon centroid
function calculatePolygonCentroid(polygon) {
    const vertices = polygon.getPath();
    let latSum = 0;
    let lngSum = 0;
    const numVertices = vertices.getLength();
    
    for (let i = 0; i < numVertices; i++) {
        const vertex = vertices.getAt(i);
        latSum += vertex.lat();
        lngSum += vertex.lng();
    }
    
    return {
        lat: latSum / numVertices,
        lng: lngSum / numVertices
    };
}

// Update calculations when polygon is edited
function updatePolygonCalculations(polygon) {
    const area = calculatePolygonArea(polygon);
    const centroid = calculatePolygonCentroid(polygon);
    const vertices = polygon.getPath();
    const pointCount = vertices.getLength();
    
    // Convert area from square meters to hectares
    const areaInHectares = area / 10000;
    
    // Update UI if elements exist
    const areaElement = document.getElementById('calculated-area');
    if (areaElement) {
        areaElement.textContent = areaInHectares.toFixed(4);
    }
    
    const sizeInput = document.getElementById('field-size') || document.getElementById('field_size');
    if (sizeInput) {
        sizeInput.value = areaInHectares.toFixed(4);
    }
    
    const centerElement = document.getElementById('calculated-center');
    if (centerElement) {
        centerElement.textContent = `${centroid.lat.toFixed(6)}, ${centroid.lng.toFixed(6)}`;
    }
    
    const pointElement = document.getElementById('point-count');
    if (pointElement) {
        pointElement.textContent = pointCount;
    }
    
    // Call update callback if defined
    if (window.onFieldPolygonUpdate) {
        window.onFieldPolygonUpdate(areaInHectares, centroid, pointCount);
    }
}

// Get polygon data for saving
window.getFieldPolygonData = function() {
    if (!currentFieldPolygon) {
        return null;
    }
    
    const vertices = currentFieldPolygon.getPath();
    const coordinates = [];
    
    for (let i = 0; i < vertices.getLength(); i++) {
        const vertex = vertices.getAt(i);
        coordinates.push({
            lat: vertex.lat(),
            lng: vertex.lng()
        });
    }
    
    const area = calculatePolygonArea(currentFieldPolygon);
    const centroid = calculatePolygonCentroid(currentFieldPolygon);
    
    return {
        coordinates: coordinates,
        area: area / 10000, // Convert to hectares
        centroid: centroid,
        pointCount: coordinates.length
    };
};

// Set map center and zoom
window.setMapLocation = function(lat, lng, zoom = 14) {
    if (fieldMap) {
        fieldMap.setCenter({ lat: lat, lng: lng });
        fieldMap.setZoom(zoom);
    }
};

// Load existing field polygon
window.loadFieldPolygon = function(coordinates) {
    clearFieldDrawing();
    
    if (!coordinates || coordinates.length < 3) {
        return;
    }
    
    const path = coordinates.map(coord => new google.maps.LatLng(coord.lat, coord.lng));
    
    currentFieldPolygon = new google.maps.Polygon({
        paths: path,
        fillColor: '#228B22',
        fillOpacity: 0.35,
        strokeWeight: 2,
        strokeColor: '#006400',
        editable: true,
        map: fieldMap
    });
    
    // Fit map to polygon bounds
    const bounds = new google.maps.LatLngBounds();
    path.forEach(point => bounds.extend(point));
    fieldMap.fitBounds(bounds);
    
    // Update calculations
    updatePolygonCalculations(currentFieldPolygon);
    
    // Add edit listeners
    google.maps.event.addListener(currentFieldPolygon.getPath(), 'set_at', function() {
        updatePolygonCalculations(currentFieldPolygon);
    });
    
    google.maps.event.addListener(currentFieldPolygon.getPath(), 'insert_at', function() {
        updatePolygonCalculations(currentFieldPolygon);
    });
    
    google.maps.event.addListener(currentFieldPolygon.getPath(), 'remove_at', function() {
        updatePolygonCalculations(currentFieldPolygon);
    });
};