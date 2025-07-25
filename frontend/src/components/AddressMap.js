import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './AddressMap.css';

// Set the Mapbox access token
const MAPBOX_TOKEN = 'pk.eyJ1IjoibmFkaXJzdWx0YW5saSIsImEiOiJjbWJ6OGxkM3IxcWZ1MmtzMXUxYzN6cXU2In0.ZYAbvebNShkCtbm-a1A8ug';
mapboxgl.accessToken = MAPBOX_TOKEN;

// Disable telemetry to prevent ad blocker issues
mapboxgl.disable = () => {};

// Check for WebGL support
if (!mapboxgl.supported()) {
  console.warn('Your browser does not support Mapbox GL');
}

const AddressMap = ({ coordinates, address }) => {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const [mapError, setMapError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    console.log('AddressMap coordinates received:', coordinates);
    console.log('AddressMap address:', address);
    
    if (!mapContainerRef.current) {
      console.log('No map container');
      setIsLoading(false);
      return;
    }

    // Check for null, undefined, or empty coordinates
    if (!coordinates || 
        coordinates === '' || 
        coordinates === 'null' || 
        coordinates === 'undefined' ||
        coordinates === null ||
        coordinates === undefined ||
        (typeof coordinates === 'string' && coordinates.trim() === '') ||
        (Array.isArray(coordinates) && coordinates.length === 0)) {
      console.log('Coordinates are empty, null, or invalid:', coordinates);
      setMapError('No location coordinates available');
      setIsLoading(false);
      return;
    }

    // Parse coordinates if they're in string format
    let lng, lat;
    
    try {
      if (typeof coordinates === 'string') {
        console.log('Parsing string coordinates:', coordinates);
        
        // First try to handle PostgreSQL POINT format: "POINT(lng lat)"
        const pointMatch = coordinates.match(/POINT\s*\(\s*([+-]?\d*\.?\d+)\s+([+-]?\d*\.?\d+)\s*\)/i);
        if (pointMatch) {
          lng = parseFloat(pointMatch[1]);
          lat = parseFloat(pointMatch[2]);
          console.log('Parsed POINT coordinates:', { lng, lat });
        } else {
          // Try to handle comma-separated format: "lng,lat" or "lat,lng"
          const parts = coordinates.split(',').map(s => s.trim());
          if (parts.length === 2) {
            // Assume lng,lat format (standard for most mapping libraries)
            lng = parseFloat(parts[0]);
            lat = parseFloat(parts[1]);
            
            // If coordinates seem reversed (lat is > 90 or < -90), swap them
            if (Math.abs(lat) > 90 && Math.abs(lng) <= 90) {
              [lng, lat] = [lat, lng];
              console.log('Swapped coordinates to correct order');
            }
            console.log('Parsed comma-separated coordinates:', { lng, lat });
          } else {
            // Try space-separated format: "lng lat"
            const spaceParts = coordinates.trim().split(/\s+/);
            if (spaceParts.length === 2) {
              lng = parseFloat(spaceParts[0]);
              lat = parseFloat(spaceParts[1]);
              console.log('Parsed space-separated coordinates:', { lng, lat });
            } else {
              console.log('Failed to parse coordinates format:', coordinates);
              setMapError('Invalid coordinate format');
              setIsLoading(false);
              return;
            }
          }
        }
      } else if (Array.isArray(coordinates)) {
        if (coordinates.length !== 2) {
          console.log('Invalid array coordinates length:', coordinates);
          setMapError('Invalid coordinate array');
          setIsLoading(false);
          return;
        }
        [lng, lat] = coordinates;
        console.log('Array coordinates:', { lng, lat });
      } else if (coordinates.lng !== undefined && coordinates.lat !== undefined) {
        lng = coordinates.lng;
        lat = coordinates.lat;
        console.log('Object coordinates:', { lng, lat });
      } else if (coordinates.longitude !== undefined && coordinates.latitude !== undefined) {
        lng = coordinates.longitude;
        lat = coordinates.latitude;
        console.log('Object coordinates (longitude/latitude):', { lng, lat });
      } else {
        console.log('Unrecognized coordinates format:', coordinates);
        setMapError('Unrecognized coordinate format');
        setIsLoading(false);
        return;
      }

      // Validate coordinates
      if (isNaN(lng) || isNaN(lat)) {
        console.log('Invalid coordinates - NaN values:', { lng, lat });
        setMapError('Invalid coordinate values (not a number)');
        setIsLoading(false);
        return;
      }

      // Validate coordinate ranges
      if (lng < -180 || lng > 180) {
        console.log('Longitude out of range:', lng);
        setMapError(`Invalid longitude: ${lng} (must be between -180 and 180)`);
        setIsLoading(false);
        return;
      }
      
      if (lat < -90 || lat > 90) {
        console.log('Latitude out of range:', lat);
        setMapError(`Invalid latitude: ${lat} (must be between -90 and 90)`);
        setIsLoading(false);
        return;
      }

      // Initialize map with a small delay to ensure container is ready
      const initMap = () => {
        if (!mapRef.current && mapContainerRef.current) {
          try {
            console.log('Initializing map with center:', [lng, lat]);
            
            // Check if container has dimensions
            const rect = mapContainerRef.current.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) {
              console.log('Container has no dimensions, retrying...');
              setTimeout(initMap, 100);
              return;
            }

            mapRef.current = new mapboxgl.Map({
              container: mapContainerRef.current,
              style: 'mapbox://styles/mapbox/streets-v12',
              center: [lng, lat],
              zoom: 15,
              interactive: true, // Allow interaction for better UX
              failIfMajorPerformanceCaveat: false,
              attributionControl: false // Hide attribution for cleaner look
            });

            // Wait for map to load
            mapRef.current.on('load', () => {
              console.log('AddressMap loaded successfully');
              setIsLoading(false);
              setMapError(null);
              
              // Ensure map resizes to fit container
              setTimeout(() => {
                if (mapRef.current) {
                  mapRef.current.resize();
                }
              }, 100);
            });

            // Handle errors
            mapRef.current.on('error', (e) => {
              console.error('AddressMap error:', e);
              setMapError('Failed to load map');
              setIsLoading(false);
            });

            // Add navigation controls
            mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

            // Add marker immediately
            addMarker();

          } catch (error) {
            console.error('Failed to initialize AddressMap:', error);
            setMapError(`Failed to initialize map: ${error.message}`);
            setIsLoading(false);
            return;
          }
        }
      };

      // Add marker function
      const addMarker = () => {
        if (mapRef.current) {
          // Remove existing marker
          if (markerRef.current) {
            markerRef.current.remove();
          }

          console.log('Adding marker at:', [lng, lat]);
          markerRef.current = new mapboxgl.Marker({
            color: '#2563eb'
          })
            .setLngLat([lng, lat])
            .addTo(mapRef.current);

          // Add popup with address info if provided
          if (address) {
            const popup = new mapboxgl.Popup({ 
              offset: 25,
              closeButton: false,
              closeOnClick: false
            })
              .setHTML(`<div class="address-popup">${address}</div>`);
            markerRef.current.setPopup(popup);
          }
        }
      };

      // Initialize map with small delay
      setTimeout(initMap, 100);

    } catch (error) {
      console.error('Error processing coordinates:', error);
      setMapError(`Error processing coordinates: ${error.message}`);
      setIsLoading(false);
      return;
    }

    // Cleanup
    return () => {
      if (markerRef.current) {
        markerRef.current.remove();
        markerRef.current = null;
      }
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [coordinates, address]);

  if (!coordinates || 
      coordinates === '' || 
      coordinates === 'null' || 
      coordinates === 'undefined' ||
      coordinates === null ||
      coordinates === undefined ||
      (typeof coordinates === 'string' && coordinates.trim() === '') ||
      (Array.isArray(coordinates) && coordinates.length === 0)) {
    return (
      <div className="address-map-container">
        <div className="no-coordinates-message">
          <p>No location coordinates available for this address</p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="address-map-container">
        <div className="no-coordinates-message">
          <p>{mapError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="address-map-container">
      {isLoading && (
        <div className="map-loading">
          <div className="loading-spinner"></div>
          <p>Loading map...</p>
        </div>
      )}
      <div 
        ref={mapContainerRef} 
        className="address-map"
        style={{ opacity: isLoading ? 0 : 1 }}
      />
    </div>
  );
};

export default AddressMap;