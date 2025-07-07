// src/useUserId.js

import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

const useUserId = () => {
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    // Check if a user ID is already stored in localStorage
    let storedUserId = localStorage.getItem('userId');

    if (storedUserId) {
      // If it exists, use it
      setUserId(storedUserId);
    } else {
      // If not, create a new one, store it, and use it
      const newUserId = uuidv4();
      localStorage.setItem('userId', newUserId);
      setUserId(newUserId);
    }
  }, []); // The empty array means this effect runs only once on component mount

  return userId;
};

export default useUserId;