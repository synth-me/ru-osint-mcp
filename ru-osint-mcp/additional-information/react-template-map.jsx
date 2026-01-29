import React, { useEffect, useRef } from 'react';

export default function Map({ points }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);

  useEffect(() => {
    if (!document.querySelector('link[href*="leaflet.min.css"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css';
      document.head.appendChild(link);
    }

    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';
    script.async = true;
    
    script.onload = () => {
      const L = window.L;
      
      if (mapInstance.current) return;

      const map = L.map(mapRef.current).setView([20, 0], 2);
      mapInstance.current = map;

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      const createCustomIcon = (color = '#3388ff') => {
        return L.divIcon({
          html: `
            <svg width="32" height="40" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 0C7.16344 0 0 7.16344 0 16C0 28 16 40 16 40S32 28 32 16C32 7.16344 24.8366 0 16 0Z" fill="${color}" stroke="white" stroke-width="2"/>
              <circle cx="16" cy="15" r="5" fill="white"/>
            </svg>
          `,
          className: 'custom-marker',
          iconSize: [32, 40],
          iconAnchor: [16, 40],
          popupAnchor: [0, -40],
        });
      };

      if (points && Array.isArray(points)) {
        points.forEach(point => {
          L.marker([point.lat, point.lng], {
            icon: createCustomIcon(point.color || '#3388ff')
          })
            .addTo(map)
            .bindPopup(point.label || 'Location');
        });
      }
    };

    document.head.appendChild(script);

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, [points]);

  return <div ref={mapRef} className="w-full h-full"></div>;
}

