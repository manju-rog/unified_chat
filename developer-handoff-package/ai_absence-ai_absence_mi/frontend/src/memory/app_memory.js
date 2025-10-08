import React, { createContext, useContext } from 'react';

// Simplified app memory context - just provides dummy functions
const AppMemoryContext = createContext();

//Dummy app memory functions that do nothing
const dummyAppMemoryFunctions = {
  showNotification: () => { },
  removeNotification: () => { },
  clearAllNotifications: () => { },
  showSuccess: () => { },
  showError: () => { },
  showWarning: () => { },
  showInfo: () => { },
  notifications: []
};

// Simplified app memory provider
export function AppMemoryProvider({ children }) {
  return (
    <AppMemoryContext.Provider value={dummyAppMemoryFunctions}>
      {children}
    </AppMemoryContext.Provider>
  );
}

// Simplified hook that returns dummy functions
export function useAppMemory() {
  const context = useContext(AppMemoryContext);
  if (!context) {
    throw new Error('useAppMemory must be used within AppMemoryProvider');
  }
  return context;
}

// Legacy exports for backward compatibility
export const useAppMemoryState = useAppMemory;
export const useAppMemoryDispatch = useAppMemory;







// app memory mostly for future use for notifications and error realated storings temperary save.