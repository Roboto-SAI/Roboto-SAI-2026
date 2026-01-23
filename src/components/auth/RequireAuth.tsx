/**
 * RequireAuth - Guards protected routes
 * Redirects to /login if not authenticated
 */

import { useEffect, useState, type ReactNode } from 'react';
import { useNavigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

interface RequireAuthProps {
  children?: ReactNode;
}

export const RequireAuth = ({ children }: RequireAuthProps) => {
  const { isLoggedIn, refreshSession } = useAuthStore();
  const navigate = useNavigate();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      const ok = await refreshSession();
      if (!active) return;
      setChecked(true);
      if (!ok) {
        navigate('/login', { replace: true });
      }
    })();
    return () => {
      active = false;
    };
  }, [refreshSession, navigate]);

  if (!checked) return null;
  if (!isLoggedIn) return null;
  
  // Support both direct children (for testing) and Outlet (for nested routes)
  return children ? <>{children}</> : <Outlet />;
};
