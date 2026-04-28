import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

const ProtectedRoute = ({ element: Component, requiredRole, ...rest }) => {
  const { isAuthenticated, userRole, isAuthLoading } = useAuth(); 
  const location = useLocation();

  if (isAuthLoading) {
    return <div>Loading...</div>;
  }

  // User roles are 0 for admin, 1 for volunteer, 2 for regular user.
  if (!isAuthenticated || userRole === null || userRole > requiredRole) {
    return <Navigate to={`/login?redirected=true&from=${location.pathname}`} />;
  }

  return <Component {...rest} />;
};

export default ProtectedRoute;