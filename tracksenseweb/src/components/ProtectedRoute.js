import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

const ProtectedRoute = ({ element: Component, requiredRole, ...rest }) => {
  const { isAuthenticated, userRole, verifyToken } = useAuth(); 
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const token = getCookie('token');
    if (token) {
      verifyToken(token).then(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [verifyToken]);

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  // User roles are 0 for admin, 1 for volunteer, 2 for regular user.
  if (!isAuthenticated || userRole === null || userRole > requiredRole) {
    return <Navigate to={`/login?redirected=true&from=${location.pathname}`} />;
  }

  return <Component {...rest} />;
};

export default ProtectedRoute;