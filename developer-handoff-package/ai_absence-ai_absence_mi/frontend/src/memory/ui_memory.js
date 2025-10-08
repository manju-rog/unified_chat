import React, { createContext, useContext, useReducer } from 'react';

// Context for UI state and dispatch
const UIMemoryStateContext = createContext();
const UIMemoryDispatchContext = createContext();

// Initial UI state - simplified without dark mode
const initialUIState = {
  currentView: 'absences',
  sidebarCollapsed: false,
  loading: {
    employees: false,
    absences: false,
    dashboard: false,
  },
  errors: {
    employees: null,
    absences: null,
    dashboard: null,
  },
};

// UI reducer for handling UI-specific state changes (without dark mode)
function uiReducer(state, action) {
  switch (action.type) {
    case 'SET_VIEW':
      return { ...state, currentView: action.payload };
    
    case 'TOGGLE_SIDEBAR':
      return { 
        ...state, 
        sidebarCollapsed: !state.sidebarCollapsed
      };
    
    case 'SET_SIDEBAR':
      return { 
        ...state, 
        sidebarCollapsed: Boolean(action.payload)
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        loading: { ...state.loading, [action.payload.key]: action.payload.loading }
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        errors: { ...state.errors, [action.payload.key]: action.payload.error }
      };
    
    case 'CLEAR_ERROR':
      return {
        ...state,
        errors: { ...state.errors, [action.payload]: null }
      };
    
    case 'CLEAR_ALL_ERRORS':
      return {
        ...state,
        errors: {
          employees: null,
          absences: null,
          dashboard: null,
        }
      };
    
    default:
      return state;
  }
}

// UI memory provider component
export function UIMemoryProvider({ children }) {
  const [state, dispatch] = useReducer(uiReducer, initialUIState);

  return (
    <UIMemoryStateContext.Provider value={state}>
      <UIMemoryDispatchContext.Provider value={dispatch}>
        {children}
      </UIMemoryDispatchContext.Provider>
    </UIMemoryStateContext.Provider>
  );
}

// Hook to access UI state
export function useUIMemoryState() {
  const context = useContext(UIMemoryStateContext);
  if (!context) {
    throw new Error('useUIMemoryState must be used within UIMemoryProvider');
  }
  return context;
}

// Hook to access UI dispatch function
export function useUIMemoryDispatch() {
  const context = useContext(UIMemoryDispatchContext);
  if (!context) {
    throw new Error('useUIMemoryDispatch must be used within UIMemoryProvider');
  }
  return context;
}

// Action creators for common UI operations (without dark mode)
export const uiActions = {
  setView: (view) => ({ type: 'SET_VIEW', payload: view }),
  toggleSidebar: () => ({ type: 'TOGGLE_SIDEBAR' }),
  setSidebar: (collapsed) => ({ type: 'SET_SIDEBAR', payload: collapsed }),
  setLoading: (key, loading) => ({ type: 'SET_LOADING', payload: { key, loading } }),
  setError: (key, error) => ({ type: 'SET_ERROR', payload: { key, error } }),
  clearError: (key) => ({ type: 'CLEAR_ERROR', payload: key }),
  clearAllErrors: () => ({ type: 'CLEAR_ALL_ERRORS' }),
};




// this is responsible for remmebering which page to view and currently viewing 
//like employyw or absence
//and side bar memoery state weather its opened or closed 
