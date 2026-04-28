import React, { createContext, useState, useContext, useEffect } from 'react';
import config from '../config';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null); // Add state for user role
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  // on mount, check for valid role via endpoint (browser sends cookie now)
  useEffect(() => {
    const verifyAuth = async() => {
      try {
        const response = await fetch(`${config.apiUrl}/role`, {
        credentials: 'include'});
        if (!response.ok) throw new Error("Not logged in");

        const data = await response.json();
        setIsAuthenticated(true);
        setUserRole(data.role);
        } catch (error) {
          setIsAuthenticated(false);
          setUserRole(null);
        } finally {
          setIsAuthLoading(false); // making sure auth checking is always done at end
        }
      };
    verifyAuth()}, []);

  const login = async () => { // in this file's context, used to check for valid role after intial load 
    const response = await fetch(`${config.apiUrl}/role`, {
        credentials: 'include'});
        if (!response.ok) return;

        const data = await response.json()
        setIsAuthenticated(true);
        setUserRole(data.role)
  };

  const logout = async () => {
    await fetch(`${config.apiUrl}/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    setIsAuthenticated(false);
    setUserRole(null); // Clear user role on logout
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, userRole, isAuthLoading, login, logout}}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);