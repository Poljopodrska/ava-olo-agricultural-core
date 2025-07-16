// Field Drawing System for AVA OLO
// Allows farmers to draw their field boundaries on a map

let fieldMap;
let currentPolygon = null;
let drawingPath = [];
let isDrawing = false;
let markers = [];

function initFieldMap() {
    console.log('initFieldMap called');
    
    // Check if Google Maps is available
    if (typeof google === 'undefined' || !google.maps) {
        console.error('Google Maps not available - check API key');
        if (window.showMapFallback) {
            window.showMapFallback('Google Maps API not loaded properly.');
        } else {
            const mapDiv = document.getElementById('field-map');
            if (mapDiv) {
                mapDiv.innerHTML = '<div style="padding: 2rem; text-align: center; background: #f8f9fa; border-radius: 8px; border: 2px dashed #dee2e6;"><h3>📍 Map Not Available</h3><p>Google Maps API key not configured. Field drawing is disabled but you can still register farmers.</p></div>';
            }
        }
        return;
    }
    
    console.log('Google Maps API loaded successfully - initializing map');
    
    try {
        // Check if map container exists
        const mapContainer = document.getElementById('field-map');
        if (!mapContainer) {
            console.error('Map container element not found');
            return;
        }
        
        // Initialize map centered on Croatia/Slovenia region (can be adjusted)
        fieldMap = new google.maps.Map(mapContainer, {
            zoom: 15,
            center: { lat: 45.8150, lng: 15.9819 }, // Zagreb coordinates as default
            mapTypeId: 'satellite', // Better for field visualization
            streetViewControl: false,
            fullscreenControl: false,
            mapTypeControl: true,
            mapTypeControlOptions: {
                style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
                mapTypeIds: ['satellite', 'hybrid', 'terrain']
            }
        });
        
        console.log('Map initialized successfully');
    } catch (error) {
        console.error('Error initializing map:', error);
        fieldMap = null;
        return;
    }

    // Try to get user's location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            if (fieldMap && typeof fieldMap.setCenter === 'function') {
                fieldMap.setCenter(userLocation);
            }
        }, function(error) {
            console.log('Geolocation error:', error);
            // Default location remains
        });
    }

    // Set up drawing event listeners
    setupDrawingListeners();
}

function setupDrawingListeners() {
    const startBtn = document.getElementById('start-drawing');
    const clearBtn = document.getElementById('clear-drawing');
    const saveBtn = document.getElementById('save-field-polygon');

    if (startBtn) startBtn.addEventListener('click', startDrawing);
    if (clearBtn) clearBtn.addEventListener('click', clearDrawing);
    if (saveBtn) saveBtn.addEventListener('click', saveFieldPolygon);

    // Map click listener for drawing
    if (fieldMap && typeof fieldMap.addListener === 'function') {
        fieldMap.addListener('click', function(event) {
            if (isDrawing) {
                addPointToField(event.latLng);
            }
        });
    } else {
        console.error('Cannot add click listener - fieldMap not initialized');
    }
}

function startDrawing() {
    isDrawing = true;
    drawingPath = [];
    clearDrawing();
    
    document.getElementById('start-drawing').textContent = '🎯 Drawing... (click map to add points)';
    document.getElementById('start-drawing').disabled = true;
    
    if (fieldMap && typeof fieldMap.setOptions === 'function') {
        fieldMap.setOptions({ draggableCursor: 'crosshair' });
    } else {
        console.error('fieldMap not initialized - cannot set cursor');
    }
    
    // Show instructions
    const instructions = document.getElementById('drawing-instructions');
    if (instructions) {
        instructions.style.display = 'block';
    }
}

function addPointToField(latLng) {
    drawingPath.push(latLng);
    
    // Add marker for this point
    const marker = new google.maps.Marker({
        position: latLng,
        map: fieldMap,
        draggable: true,
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: '#FFD700',
            fillOpacity: 1,
            strokeColor: '#FF8C00',
            strokeWeight: 2
        },
        title: `Point ${markers.length + 1}`
    });
    
    // Add point number label
    const label = new google.maps.Marker({
        position: latLng,
        map: fieldMap,
        label: {
            text: String(markers.length + 1),
            color: 'white',
            fontSize: '12px',
            fontWeight: 'bold'
        },
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 0
        }
    });
    
    markers.push(marker);
    
    // Make marker draggable to edit field shape
    marker.addListener('drag', function() {
        updatePolygonFromMarkers();
    });
    
    // Double-click to remove point
    marker.addListener('dblclick', function() {
        removePoint(marker);
    });
    
    // Update or create polygon
    updatePolygon();
    
    // Update UI
    document.getElementById('point-count').textContent = drawingPath.length;
    
    // If we have at least 3 points, show the calculations
    if (drawingPath.length >= 3) {
        calculateFieldData();
        document.getElementById('field-calculations').style.display = 'block';
    }
    
    // Check if we should auto-close the polygon
    if (drawingPath.length > 2) {
        const firstPoint = drawingPath[0];
        const distance = google.maps.geometry.spherical.computeDistanceBetween(latLng, firstPoint);
        
        // If clicked near the first point (within 20 meters), close the polygon
        if (distance < 20) {
            finishDrawing();
        }
    }
}

function removePoint(markerToRemove) {
    const index = markers.indexOf(markerToRemove);
    if (index > -1) {
        markers[index].setMap(null);
        markers.splice(index, 1);
        updatePolygonFromMarkers();
        
        // Update point numbers
        markers.forEach((marker, i) => {
            marker.setTitle(`Point ${i + 1}`);
        });
    }
}

function finishDrawing() {
    isDrawing = false;
    document.getElementById('start-drawing').textContent = '🎯 Start Drawing Field';
    document.getElementById('start-drawing').disabled = false;
    if (fieldMap && typeof fieldMap.setOptions === 'function') {
        fieldMap.setOptions({ draggableCursor: null });
    }
    
    // Hide instructions
    const instructions = document.getElementById('drawing-instructions');
    if (instructions) {
        instructions.style.display = 'none';
    }
    
    // Enable save button
    document.getElementById('save-field-polygon').disabled = false;
}

function updatePolygon() {
    if (currentPolygon) {
        currentPolygon.setMap(null);
    }
    
    if (drawingPath.length >= 2) {
        currentPolygon = new google.maps.Polygon({
            paths: drawingPath,
            strokeColor: '#FFD700', // Yellow as requested
            strokeOpacity: 1.0,
            strokeWeight: 3,
            fillColor: '#8BC34A',
            fillOpacity: 0.3,
            editable: false // We handle editing with markers
        });
        
        currentPolygon.setMap(fieldMap);
    }
}

function updatePolygonFromMarkers() {
    drawingPath = markers.map(marker => marker.getPosition());
    updatePolygon();
    calculateFieldData();
}

function calculateFieldData() {
    if (drawingPath.length < 3) return;
    
    // Calculate area using Google Maps geometry library
    const area = google.maps.geometry.spherical.computeArea(drawingPath);
    const areaInHectares = (area / 10000).toFixed(4); // Convert to hectares with 4 decimal places
    
    // Calculate centroid (simple average method)
    let lat = 0, lng = 0;
    drawingPath.forEach(point => {
        lat += point.lat();
        lng += point.lng();
    });
    
    const centroid = {
        lat: (lat / drawingPath.length).toFixed(8),
        lng: (lng / drawingPath.length).toFixed(8)
    };
    
    // Update UI
    document.getElementById('calculated-area').textContent = areaInHectares;
    document.getElementById('calculated-center').textContent = `${centroid.lat}, ${centroid.lng}`;
    
    // Auto-fill the form fields for the current field being edited
    const fieldIndex = getCurrentFieldIndex();
    if (fieldIndex !== null) {
        const sizeInput = document.getElementById(`field_size_${fieldIndex}`);
        const locationInput = document.getElementById(`field_location_${fieldIndex}`);
        
        if (sizeInput) {
            sizeInput.value = areaInHectares;
        }
        
        if (locationInput) {
            locationInput.value = `${centroid.lat}, ${centroid.lng}`;
        }
    }
}

function getCurrentFieldIndex() {
    // Get the currently active field index from the UI
    const activeField = document.querySelector('.field-entry.active');
    if (activeField) {
        return parseInt(activeField.dataset.fieldIndex);
    }
    
    // Default to the last field
    const allFields = document.querySelectorAll('.field-entry');
    if (allFields.length > 0) {
        return parseInt(allFields[allFields.length - 1].dataset.fieldIndex);
    }
    
    return 0;
}

function clearDrawing() {
    // Clear polygon
    if (currentPolygon) {
        currentPolygon.setMap(null);
        currentPolygon = null;
    }
    
    // Clear markers
    if (markers && Array.isArray(markers)) {
        markers.forEach(marker => {
            if (marker && typeof marker.setMap === 'function') {
                marker.setMap(null);
            }
        });
        markers = [];
    }
    
    // Reset drawing state
    drawingPath = [];
    isDrawing = false;
    
    // Reset UI
    document.getElementById('start-drawing').textContent = '🎯 Start Drawing Field';
    document.getElementById('start-drawing').disabled = false;
    document.getElementById('field-calculations').style.display = 'none';
    document.getElementById('point-count').textContent = '0';
    document.getElementById('save-field-polygon').disabled = true;
    document.getElementById('save-field-polygon').textContent = '💾 Save Field Shape';
    
    if (fieldMap && typeof fieldMap.setOptions === 'function') {
        fieldMap.setOptions({ draggableCursor: null });
    }
    
    // Hide instructions
    const instructions = document.getElementById('drawing-instructions');
    if (instructions) {
        instructions.style.display = 'none';
    }
}

function saveFieldPolygon() {
    if (drawingPath.length < 3) {
        alert('Please draw a field with at least 3 points');
        return;
    }
    
    // Convert coordinates to simple format for database storage
    const coordinates = drawingPath.map(point => ({
        lat: point.lat(),
        lng: point.lng()
    }));
    
    // Calculate centroid for location
    let lat = 0, lng = 0;
    coordinates.forEach(coord => {
        lat += coord.lat;
        lng += coord.lng;
    });
    
    const centroid = {
        lat: lat / coordinates.length,
        lng: lng / coordinates.length
    };
    
    // Calculate area
    const area = google.maps.geometry.spherical.computeArea(drawingPath);
    const areaInHectares = (area / 10000).toFixed(4);
    
    // Store in a hidden field or add to the form data
    const polygonData = {
        coordinates: coordinates,
        centroid: centroid,
        area: parseFloat(areaInHectares),
        created_at: new Date().toISOString()
    };
    
    // Get current field index
    const fieldIndex = getCurrentFieldIndex();
    
    // Add hidden input to store polygon data for this field
    let polygonInput = document.getElementById(`field_polygon_data_${fieldIndex}`);
    if (!polygonInput) {
        polygonInput = document.createElement('input');
        polygonInput.type = 'hidden';
        polygonInput.id = `field_polygon_data_${fieldIndex}`;
        polygonInput.name = `fields[${fieldIndex}][polygon_data]`;
        const fieldEntry = document.querySelector(`.field-entry[data-field-index="${fieldIndex}"]`);
        if (fieldEntry) {
            fieldEntry.appendChild(polygonInput);
        }
    }
    
    polygonInput.value = JSON.stringify(polygonData);
    
    // Visual feedback
    alert(`✅ Field shape saved! Area: ${areaInHectares} hectares`);
    document.getElementById('save-field-polygon').textContent = '✅ Field Shape Saved';
    document.getElementById('save-field-polygon').disabled = true;
    
    // Mark the field entry as having polygon data
    const fieldEntry = document.querySelector(`.field-entry[data-field-index="${fieldIndex}"]`);
    if (fieldEntry) {
        fieldEntry.classList.add('has-polygon');
        
        // Add visual indicator
        let indicator = fieldEntry.querySelector('.polygon-indicator');
        if (!indicator) {
            indicator = document.createElement('span');
            indicator.className = 'polygon-indicator';
            indicator.style.cssText = 'color: #4CAF50; margin-left: 10px; font-weight: bold;';
            indicator.textContent = '🗺️ Map data saved';
            const fieldNameLabel = fieldEntry.querySelector('label[for^="field_name"]');
            if (fieldNameLabel) {
                fieldNameLabel.appendChild(indicator);
            }
        }
    }
}

// Function to highlight the active field being edited
function setActiveField(fieldIndex) {
    // Remove active class from all fields
    document.querySelectorAll('.field-entry').forEach(entry => {
        entry.classList.remove('active');
    });
    
    // Add active class to the selected field
    const activeField = document.querySelector(`.field-entry[data-field-index="${fieldIndex}"]`);
    if (activeField) {
        activeField.classList.add('active');
        activeField.style.backgroundColor = '#f0f8ff';
        activeField.style.border = '2px solid #4CAF50';
    }
    
    // Clear any existing drawing
    clearDrawing();
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers to field entries to make them selectable
    document.addEventListener('click', function(e) {
        const fieldEntry = e.target.closest('.field-entry');
        if (fieldEntry) {
            const fieldIndex = fieldEntry.dataset.fieldIndex;
            setActiveField(fieldIndex);
        }
    });
    
    console.log('Field drawing system ready');
});

// Make functions available globally
window.initFieldMap = initFieldMap;
window.setActiveField = setActiveField;