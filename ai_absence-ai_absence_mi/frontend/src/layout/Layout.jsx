// Main layout wrapper component
import React, { useEffect, useCallback } from 'react';
import { useUIMemoryState, useUIMemoryDispatch } from '../memory/ui_memory';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import MainArea from './MainArea';
import Chatbot from '../components/Chatbot/Chatbot';
import '../css_design/components/Layout/Layout.css';

// Layout component with responsive handling
const Layout = React.memo(({ children }) => {
  const { sidebarCollapsed } = useUIMemoryState();
  const dispatch = useUIMemoryDispatch();
  
  useEffect(() => {
    const root = document.documentElement;
    // Default to light mode since dark mode is not implemented yet
    root.setAttribute('data-color-scheme', 'light');
  }, []);
  
  // Simple responsive handling - only auto-collapse on mobile, never auto-expand
  const handleResize = useCallback(() => {
    const isMobile = window.innerWidth <= 768;
    
    // Only auto-collapse on mobile if sidebar is currently open
    if (isMobile && !sidebarCollapsed) {
      dispatch({ type: 'SET_SIDEBAR', payload: true });
    }
  }, [dispatch, sidebarCollapsed]);

  useEffect(() => {
    // Set initial state based on screen size
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
      dispatch({ type: 'SET_SIDEBAR', payload: true });
    }
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [handleResize, dispatch]);
  
  return (
    <div className="app-layout">
      <TopBar />
      <Sidebar />
      <MainArea>
        {children}
      </MainArea>
      <Chatbot />
    </div>
  );
});

export default Layout;