import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';
import '@mapbox/mapbox-gl-geocoder/dist/mapbox-gl-geocoder.css';
import 'mapbox-gl/dist/mapbox-gl.css';
import './MapboxAddressInput.css';

// Set the Mapbox access token
const MAPBOX_TOKEN = 'pk.eyJ1IjoibmFkaXJzdWx0YW5saSIsImEiOiJjbWJ6OGxkM3IxcWZ1MmtzMXUxYzN6cXU2In0.ZYAbvebNShkCtbm-a1A8ug';
mapboxgl.accessToken = MAPBOX_TOKEN;

// Disable telemetry to prevent ad blocker issues
mapboxgl.disable = () => {};

// Check for WebGL support
if (!mapboxgl.supported()) {
  console.warn('Your browser does not support Mapbox GL');
}

const MapboxAddressInput = ({ 
  onAddressSelect, 
  onCoordinatesChange, 
  initialCoordinates = null,
  placeholder = "Search for an address..."
}) => {
  const geocoderContainerRef = useRef(null);
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const geocoderRef = useRef(null);
  const [isMapVisible, setIsMapVisible] = useState(false);
  const [selectedAddress, setSelectedAddress] = useState(null);

  useEffect(() => {
    if (!geocoderContainerRef.current) return;

    // First, test token permissions
    testTokenPermissions();

    // Clear any existing geocoder
    if (geocoderRef.current) {
      const existingGeocoder = geocoderContainerRef.current.querySelector('.mapboxgl-ctrl-geocoder');
      if (existingGeocoder) {
        existingGeocoder.remove();
      }
    }

    // Initialize the geocoder with more permissive settings
    const geocoder = new MapboxGeocoder({
      accessToken: MAPBOX_TOKEN,
      // Use broader types for better results
      types: 'address,poi,place,locality,neighborhood',
      placeholder: placeholder,
      // Don't restrict to country initially
      language: 'en',
      limit: 10,
      // Set proximity to Kenya but allow global results
      proximity: {
        longitude: 36.8219,  // Nairobi coordinates
        latitude: -1.2921
      },
      mapboxgl: mapboxgl,
      // Disable flyTo and marker as we handle them manually
      flyTo: false,
      marker: false,
      // Don't use bounding box initially - it might be too restrictive
      // bbox: [33.8935, -4.6796, 41.8550, 5.5067],
      
      // Custom local geocoder for debugging
      localGeocoder: (query) => {
        console.log('Local geocoder called with query:', query);
        return [];
      },
      
      // More permissive filter
      filter: (item) => {
        console.log('Filtering item:', item);
        // Always return true to allow all results
        return true;
      },
      
      // Add custom rendering
      render: function(item) {
        console.log('Rendering item:', item);
        return item.place_name;
      },
      
      // Add getItemValue for custom handling
      getItemValue: function(item) {
        console.log('Getting item value:', item);
        return item.place_name;
      }
    });

    geocoderRef.current = geocoder;

    // Add the geocoder to the container
    geocoderContainerRef.current.appendChild(geocoder.onAdd());

    // Handle result selection
    const handleResult = (e) => {
      const result = e.result;
      const coordinates = result.geometry.coordinates;
      
      setSelectedAddress({
        address: result.place_name,
        coordinates: coordinates,
        properties: result.properties
      });

      // Parse the address components
      const addressComponents = parseMapboxAddress(result);
      
      // Call the callback with the address data
      onAddressSelect(addressComponents);
      onCoordinatesChange(coordinates);
      
      // Show the map
      setIsMapVisible(true);
      
      // Initialize or update the map
      setTimeout(() => {
        initializeMap(coordinates);
      }, 100);
    };

    // Handle clearing
    const handleClear = () => {
      setSelectedAddress(null);
      setIsMapVisible(false);
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };

    // Handle errors
    const handleError = (e) => {
      console.error('Mapbox Geocoder Error:', e);
      if (e && e.error) {
        console.error('Error details:', e.error);
      }
    };

    geocoder.on('result', handleResult);
    geocoder.on('clear', handleClear);
    geocoder.on('error', handleError);

    // Comprehensive event logging
    geocoder.on('loading', (e) => {
      console.log('Geocoder loading:', e);
    });

    geocoder.on('results', (e) => {
      console.log('Geocoder results:', e);
      console.log('Number of features returned:', e.features ? e.features.length : 0);
      
      if (e.features && e.features.length === 0) {
        console.log('No results found for query:', e.query);
        console.log('Trying manual API call for debugging...');
        
        // Make a direct API call to test
        testDirectApiCall(e.query[0]);
      } else if (e.features) {
        console.log('Found results:', e.features.map(f => f.place_name));
      }
    });

    // Add response event listener
    geocoder.on('response', (e) => {
      console.log('Geocoder raw response:', e);
    });

    return () => {
      if (geocoder) {
        geocoder.off('result', handleResult);
        geocoder.off('clear', handleClear);
        geocoder.off('error', handleError);
      }
      if (geocoderRef.current) {
        const existingGeocoder = geocoderContainerRef.current?.querySelector('.mapboxgl-ctrl-geocoder');
        if (existingGeocoder) {
          existingGeocoder.remove();
        }
      }
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Test token permissions
  const testTokenPermissions = async () => {
    try {
      console.log('Testing token permissions...');
      const testUrl = `https://api.mapbox.com/geocoding/v5/mapbox.places/nairobi.json?access_token=${MAPBOX_TOKEN}`;
      const response = await fetch(testUrl);
      const data = await response.json();
      
      if (response.ok) {
        console.log('✅ Token works! Test query returned:', data.features ? data.features.length : 0, 'results');
        if (data.features && data.features.length > 0) {
          console.log('Sample result:', data.features[0].place_name);
        }
      } else {
        console.error('❌ Token permission error:', data);
        if (data.message && data.message.includes('Invalid token')) {
          console.error('The Mapbox token is invalid or expired');
        } else if (data.message && data.message.includes('Not Authorized')) {
          console.error('The Mapbox token does not have geocoding permissions');
        }
      }
    } catch (error) {
      console.error('❌ Token test failed:', error);
    }
  };

  // Test direct API call function
  const testDirectApiCall = async (query) => {
    try {
      console.log('Testing direct API call for:', query);
      
      // Test 1: Global search
      const globalUrl = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${MAPBOX_TOKEN}&limit=5`;
      console.log('Global API URL:', globalUrl);
      
      const globalResponse = await fetch(globalUrl);
      const globalData = await globalResponse.json();
      console.log('Global API response:', globalData);
      console.log('Global features count:', globalData.features ? globalData.features.length : 0);
      if (globalData.features && globalData.features.length > 0) {
        console.log('Global results:', globalData.features.map(f => f.place_name));
      }
      
      // Test 2: Kenya-specific search
      const kenyaUrl = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${MAPBOX_TOKEN}&country=ke&limit=5&proximity=36.8219,-1.2921`;
      console.log('Kenya API URL:', kenyaUrl);
      
      const kenyaResponse = await fetch(kenyaUrl);
      const kenyaData = await kenyaResponse.json();
      console.log('Kenya API response:', kenyaData);
      console.log('Kenya features count:', kenyaData.features ? kenyaData.features.length : 0);
      if (kenyaData.features && kenyaData.features.length > 0) {
        console.log('Kenya results:', kenyaData.features.map(f => f.place_name));
      }
      
      // Test 3: Places search (broader)
      const placesUrl = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${MAPBOX_TOKEN}&types=place,locality,neighborhood&proximity=36.8219,-1.2921&limit=5`;
      console.log('Places API URL:', placesUrl);
      
      const placesResponse = await fetch(placesUrl);
      const placesData = await placesResponse.json();
      console.log('Places API response:', placesData);
      console.log('Places features count:', placesData.features ? placesData.features.length : 0);
      if (placesData.features && placesData.features.length > 0) {
        console.log('Places results:', placesData.features.map(f => f.place_name));
      }
      
    } catch (error) {
      console.error('Direct API test failed:', error);
    }
  };

  // Initialize map with coordinates
  useEffect(() => {
    if (initialCoordinates && initialCoordinates.length === 2) {
      setIsMapVisible(true);
      setTimeout(() => {
        initializeMap(initialCoordinates);
      }, 100);
    }
  }, [initialCoordinates]);

  const parseMapboxAddress = (result) => {
    const context = result.context || [];
    let street = '';
    let city = '';
    let state = '';
    let country = 'Kenya';
    let zip_code = '';

    // Extract street from place_name
    if (result.place_name) {
      // Remove country from the end if present
      const addressParts = result.place_name.split(',').map(part => part.trim());
      
      // If it's a POI (Point of Interest), use the POI name + address
      if (result.properties && result.properties.address) {
        street = `${result.text}, ${result.properties.address}`;
      } else {
        // Otherwise, use the first part as street
        street = addressParts[0] || result.text || '';
      }
    }

    // Parse context for other components
    context.forEach(item => {
      if (item.id.includes('place')) {
        city = item.text;
      } else if (item.id.includes('region')) {
        state = item.text;
      } else if (item.id.includes('country')) {
        country = item.text;
      } else if (item.id.includes('postcode')) {
        zip_code = item.text;
      } else if (item.id.includes('locality') && !city) {
        // Sometimes city is marked as locality
        city = item.text;
      } else if (item.id.includes('district') && !state) {
        // In Kenya, districts can be used as state/province
        state = item.text;
      }
    });

    // For Kenya, if no city was found, try to extract from place_name
    if (!city && result.place_name) {
      const parts = result.place_name.split(',');
      if (parts.length > 1) {
        city = parts[1].trim();
      }
    }

    return {
      street: street,
      city: city || 'Nairobi', // Default to Nairobi if no city found
      state: state,
      country: country,
      zip_code: zip_code
    };
  };

  const initializeMap = (coordinates) => {
    if (!mapContainerRef.current) return;

    // Remove existing map
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    try {
      // Create new map
      const map = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: coordinates,
        zoom: 15,
        attributionControl: false,
        failIfMajorPerformanceCaveat: false // Allow map to work even with performance issues
      });

      mapRef.current = map;

      // Wait for map to load
      map.on('load', () => {
        console.log('Map loaded successfully');
        map.resize(); // Ensure proper sizing
      });

      // Handle errors
      map.on('error', (e) => {
        console.error('Map error:', e);
      });

      // Add marker
      const marker = new mapboxgl.Marker({
        draggable: true,
        color: '#667eea'
      })
        .setLngLat(coordinates)
        .addTo(map);

      markerRef.current = marker;

      // Handle marker drag
      marker.on('dragend', () => {
        const lngLat = marker.getLngLat();
        const newCoordinates = [lngLat.lng, lngLat.lat];
        onCoordinatesChange(newCoordinates);
        
        // Optionally, reverse geocode to get the address
        reverseGeocode(newCoordinates);
      });

      // Add map controls
      map.addControl(new mapboxgl.NavigationControl(), 'top-right');

      // Handle map click to move marker
      map.on('click', (e) => {
        const coordinates = [e.lngLat.lng, e.lngLat.lat];
        marker.setLngLat(coordinates);
        onCoordinatesChange(coordinates);
        reverseGeocode(coordinates);
      });
    } catch (error) {
      console.error('Failed to initialize map:', error);
    }
  };

  const reverseGeocode = async (coordinates) => {
    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${coordinates[0]},${coordinates[1]}.json?access_token=${MAPBOX_TOKEN}&types=address,poi&country=ke&language=en`
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.features && data.features.length > 0) {
          const result = data.features[0];
          const addressComponents = parseMapboxAddress(result);
          onAddressSelect(addressComponents);
          
          setSelectedAddress({
            address: result.place_name,
            coordinates: coordinates,
            properties: result.properties
          });
        }
      }
    } catch (error) {
      console.error('Reverse geocoding failed:', error);
    }
  };

  return (
    <div className="mapbox-address-input">
      <div className="geocoder-container" ref={geocoderContainerRef} />
      
      {isMapVisible && (
        <div className="map-container">
          <div className="map-header">
            <h4>Adjust Pin Location</h4>
            <p>Drag the pin or click on the map to adjust the exact location</p>
          </div>
          <div 
            ref={mapContainerRef} 
            className="map" 
            style={{ height: '300px', width: '100%' }}
          />
          {selectedAddress && (
            <div className="selected-address">
              <strong>Selected Address:</strong>
              <p>{selectedAddress.address}</p>
              <small>
                Coordinates: {selectedAddress.coordinates[1].toFixed(6)}, {selectedAddress.coordinates[0].toFixed(6)}
              </small>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MapboxAddressInput;