import React, { useEffect, useRef } from 'react';
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

  useEffect(() => {
    console.log('AddressMap coordinates received:', coordinates);
    console.log('AddressMap address:', address);
    
    if (!mapContainerRef.current || !coordinates) {
      console.log('No map container or coordinates');
      return;
    }

    // Parse coordinates if they're in string format
    let lng, lat;
    if (typeof coordinates === 'string') {
      console.log('Parsing string coordinates:', coordinates);
      // Handle PostgreSQL POINT format: "POINT(lng lat)"
      const match = coordinates.match(/POINT\(([^ ]+) ([^ ]+)\)/);
      if (match) {
        lng = parseFloat(match[1]);
        lat = parseFloat(match[2]);
        console.log('Parsed coordinates:', { lng, lat });
      } else {
        console.log('Failed to parse coordinates format:', coordinates);
        return;
      }
    } else if (Array.isArray(coordinates)) {
      [lng, lat] = coordinates;
      console.log('Array coordinates:', { lng, lat });
    } else if (coordinates.lng && coordinates.lat) {
      lng = coordinates.lng;
      lat = coordinates.lat;
      console.log('Object coordinates:', { lng, lat });
    } else {
      console.log('Unrecognized coordinates format:', coordinates);
      return;
    }

    // Validate coordinates
    if (isNaN(lng) || isNaN(lat)) {
      console.log('Invalid coordinates - NaN values:', { lng, lat });
      return;
    }

    // Initialize map with a small delay to ensure container is ready
    const initMap = () => {
      if (!mapRef.current && mapContainerRef.current) {
        try {
          console.log('Initializing map with center:', [lng, lat]);
          mapRef.current = new mapboxgl.Map({
            container: mapContainerRef.current,
            style: 'mapbox://styles/mapbox/streets-v12',
            center: [lng, lat],
            zoom: 15,
            interactive: false, // Make map non-interactive for display only
            failIfMajorPerformanceCaveat: false
          });

          // Wait for map to load
          mapRef.current.on('load', () => {
            console.log('AddressMap loaded successfully');
            mapRef.current.resize();
          });

          // Handle errors
          mapRef.current.on('error', (e) => {
            console.error('AddressMap error:', e);
          });

          // Add navigation controls
          mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
        } catch (error) {
          console.error('Failed to initialize AddressMap:', error);
          return;
        }
      }
    };

    // Initialize map with small delay
    setTimeout(initMap, 100);

    // Add marker after map is ready
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
          const popup = new mapboxgl.Popup({ offset: 25 })
            .setHTML(`<div class="address-popup">${address}</div>`);
          markerRef.current.setPopup(popup);
        }

        // Center map on coordinates
        mapRef.current.flyTo({
          center: [lng, lat],
          zoom: 15
        });
      } else {
        // If map isn't ready yet, try again in a bit
        setTimeout(addMarker, 200);
      }
    };

    // Add marker with delay to ensure map is initialized
    setTimeout(addMarker, 200);

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

  if (!coordinates) {
    return (
      <div className="address-map-container">
        <div className="no-coordinates-message">
          <p>No location data available for this address</p>
        </div>
      </div>
    );
  }

  return (
    <div className="address-map-container">
      <div ref={mapContainerRef} className="address-map" />
    </div>
  );
};

export default AddressMap;