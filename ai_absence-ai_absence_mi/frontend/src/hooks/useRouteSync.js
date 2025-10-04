import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useUIMemoryDispatch } from '../memory/ui_memory';

// Hook to sync route changes with UI memory
const useRouteSync = () => {
  const location = useLocation();
  const dispatch = useUIMemoryDispatch();

  useEffect(() => {
    // Map routes to view names for backward compatibility
    const routeToViewMap = {
      '/dashboard': 'dashboard',
      '/absences': 'absences',
      '/employees': 'employees',
      '/add-employee': 'employees', // Same view, different route
      '/reports': 'reports'
    };

    const currentView = routeToViewMap[location.pathname] || 'dashboard';
    dispatch({ type: 'SET_VIEW', payload: currentView });
  }, [location.pathname, dispatch]);
};

export default useRouteSync;