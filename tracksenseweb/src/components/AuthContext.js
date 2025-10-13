import React, { createContext, useState, useContext, useEffect } from 'react';
import config from '../config';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null); // Add state for user role

  useEffect(() => {
    const token = getCookie('token');
    if (token) {
      verifyToken(token);
    }
  }, []);

  const login = () => {
    setIsAuthenticated(true);
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUserRole(null); // Clear user role on logout
    document.cookie = 'token=; path=/; max-age=0'; // Remove the token cookie
  };

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  };

  const verifyToken = async (token) => {
    try {
      const response = await fetch(`${config.apiUrl}/verify-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      if (data.valid) {
        setIsAuthenticated(true);

        // Fetch user role
        const roleResponse = await fetch(`${config.apiUrl}/role`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        const roleData = await roleResponse.json();
        setUserRole(roleData.role); // Store user role in state
      } else {
        setIsAuthenticated(false);
        setUserRole(null);
        document.cookie = 'token=; path=/; max-age=0'; // Remove the token cookie
      }
    } catch (error) {
      console.error('Error verifying token:', error);
      setIsAuthenticated(false);
      setUserRole(null);
      document.cookie = 'token=; path=/; max-age=0'; // Remove the token cookie
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, userRole, login, logout, verifyToken }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);