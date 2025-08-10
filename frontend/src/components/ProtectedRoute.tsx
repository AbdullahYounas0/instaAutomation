import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { authService } from '../services/authService';

interface ProtectedRouteProps {
  children: React.ReactNode;
  adminOnly?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, adminOnly = false }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const token = authService.getToken();
      const user = authService.getCurrentUser();

      if (!token || !user) {
        setIsAuthenticated(false);
        return;
      }

      try {
        const result = await authService.verifyToken(token);
        if (result.success) {
          setIsAuthenticated(true);
          setIsAdmin(user.role === 'admin');
        } else {
          // Token is invalid, clear storage
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, []);

  // Show loading while checking authentication
  if (isAuthenticated === null) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '1.1rem',
        color: '#6c757d'
      }}>
        Verifying authentication...
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Redirect to login if admin access required but user is not admin
  if (adminOnly && !isAdmin) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
