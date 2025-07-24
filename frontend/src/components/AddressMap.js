import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './AddressMap.css';

// Set the Mapbox access token
const MAPBOX_TOKEN = 'pk.eyJ1IjoibmFkaXJzdWx0YW5saSIsImEiOiJjbWJ6OGxkM3IxcWZ1MmtzMXUxYzN6cXU2In0.ZYAbvebNShkCtbm-a1A8ug';
mapboxgl.accessToken = MAPBOX_TOKEN;

const AddressMap = ({ coordinates, address }) => {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current || !coordinates) return;

    // Parse coordinates if they're in string format
    let lng, lat;
    if (typeof coordinates === 'string') {
      // Handle PostgreSQL POINT format: "POINT(lng lat)"
      const match = coordinates.match(/POINT\(([^ ]+) ([^ ]+)\)/);
      if (match) {
        lng = parseFloat(match[1]);
        lat = parseFloat(match[2]);
      } else {
        return;
      }
    } else if (Array.isArray(coordinates)) {
      [lng, lat] = coordinates;
    } else if (coordinates.lng && coordinates.lat) {
      lng = coordinates.lng;
      lat = coordinates.lat;
    } else {
      return;
    }

    // Initialize map
    if (!mapRef.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [lng, lat],
        zoom: 15,
        interactive: false // Make map non-interactive for display only
      });

      // Add navigation controls
      mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    }

    // Add or update marker
    if (markerRef.current) {
      markerRef.current.remove();
    }

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

    // Cleanup
    return () => {
      if (markerRef.current) {
        markerRef.current.remove();
      }
    };
  }, [coordinates, address]);

  if (!coordinates) {
    return null;
  }

  return (
    <div className="address-map-container">
      <div ref={mapContainerRef} className="address-map" />
    </div>
  );
};

export default AddressMap;