// src/useUserId.js

import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

const useUserId = () => {
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    // First, check if there's a session ID in the URL path
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    const urlSessionId = pathSegments[0]; // First segment after domain
    
    // Check if a user ID is already stored in localStorage
    let storedUserId = localStorage.getItem('userId');

    if (urlSessionId && urlSessionId.length > 10) { // Basic validation for UUID-like session ID
      // If session ID is in URL path, use it and update localStorage
      setUserId(urlSessionId);
      localStorage.setItem('userId', urlSessionId);
    } else if (storedUserId) {
      // If no URL session ID but localStorage has one, use it and update URL
      setUserId(storedUserId);
      
      // Add session ID to URL path
      const newPath = `/${storedUserId}`;
      window.history.replaceState({}, '', newPath);
    } else {
      // If neither exists, create a new one
      const newUserId = uuidv4();
      setUserId(newUserId);
      localStorage.setItem('userId', newUserId);
      
      // Add session ID to URL path
      const newPath = `/${newUserId}`;
      window.history.replaceState({}, '', newPath);
    }
  }, []); // The empty array means this effect runs only once on component mount

  return userId;
};

export default useUserId;