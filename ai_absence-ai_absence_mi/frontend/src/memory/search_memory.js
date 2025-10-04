import React, { createContext, useContext, useReducer, useMemo, useCallback } from 'react';

// Context for search state and dispatch
const SearchMemoryStateContext = createContext();
const SearchMemoryDispatchContext = createContext();

// Initial search state
const initialSearchState = {
  query: '',
  filters: {
    department: '',
    location: '',
    role: '',
    absenceType: '',
  },
  results: {
    employees: [],
    absences: [],
  },
  isSearching: false,
  searchHistory: [],
  suggestions: [],
  activeSearchType: 'all', // 'all', 'employees', 'absences'
};

// Search reducer for handling search-related state changes
function searchReducer(state, action) {
  switch (action.type) {
    case 'SET_QUERY':
      return { 
        ...state, 
        query: action.payload,
        // Clear results when query changes
        results: action.payload === '' ? { employees: [], absences: [] } : state.results
      };
    
    case 'SET_FILTER':
      return {
        ...state,
        filters: { ...state.filters, [action.payload.key]: action.payload.value }
      };
    
    case 'CLEAR_FILTERS':
      return {
        ...state,
        filters: {
          department: '',
          location: '',
          role: '',
          absenceType: '',
        }
      };
    
    case 'SET_SEARCH_TYPE':
      return { ...state, activeSearchType: action.payload };
    
    case 'SEARCH_START':
      return { ...state, isSearching: true };
    
    case 'SEARCH_SUCCESS':
      return {
        ...state,
        isSearching: false,
        results: action.payload,
        // Add to search history if query is not empty
        searchHistory: state.query.trim() !== '' && !state.searchHistory.includes(state.query.trim())
          ? [state.query.trim(), ...state.searchHistory.slice(0, 9)] // Keep last 10 searches
          : state.searchHistory
      };
    
    case 'SEARCH_ERROR':
      return {
        ...state,
        isSearching: false,
        results: { employees: [], absences: [] }
      };
    
    case 'SET_SUGGESTIONS':
      return { ...state, suggestions: action.payload };
    
    case 'CLEAR_SEARCH':
      return {
        ...state,
        query: '',
        results: { employees: [], absences: [] },
        suggestions: []
      };
    
    case 'CLEAR_SEARCH_HISTORY':
      return { ...state, searchHistory: [] };
    
    default:
      return state;
  }
}

// Search memory provider component
export function SearchMemoryProvider({ children }) {
  const [state, dispatch] = useReducer(searchReducer, initialSearchState);

  // Memoized search operations
  const searchOperations = useMemo(() => {
    // Search employees based on query and filters
    const searchEmployees = (employees, query, filters) => {
      if (!employees || employees.length === 0) return [];
      
      let filtered = employees;
      
      // Apply text search
      if (query.trim()) {
        const searchTerm = query.toLowerCase().trim();
        filtered = filtered.filter(employee => 
          employee.name?.toLowerCase().includes(searchTerm) ||
          employee.email?.toLowerCase().includes(searchTerm) ||
          employee.department?.toLowerCase().includes(searchTerm) ||
          employee.role?.toLowerCase().includes(searchTerm) ||
          employee.location?.toLowerCase().includes(searchTerm)
        );
      }
      
      // Apply filters
      if (filters.department) {
        filtered = filtered.filter(employee => employee.department === filters.department);
      }
      
      if (filters.location) {
        filtered = filtered.filter(employee => employee.location === filters.location);
      }
      
      if (filters.role) {
        filtered = filtered.filter(employee => employee.role === filters.role);
      }
      
      return filtered;
    };

    // Search absences based on query and filters
    const searchAbsences = (absences, employees, query, filters) => {
      if (!absences || absences.length === 0) return [];
      
      let filtered = absences;
      
      // Apply text search
      if (query.trim()) {
        const searchTerm = query.toLowerCase().trim();
        filtered = filtered.filter(absence => {
          const employee = employees.find(emp => emp.id === absence.employeeId);
          return (
            employee?.name?.toLowerCase().includes(searchTerm) ||
            absence.absenceType?.toLowerCase().includes(searchTerm) ||
            absence.reason?.toLowerCase().includes(searchTerm) ||
            absence.absenceDate?.includes(searchTerm)
          );
        });
      }
      
      // Apply absence type filter
      if (filters.absenceType) {
        filtered = filtered.filter(absence => absence.absenceType === filters.absenceType);
      }
      
      // Apply employee-based filters
      if (filters.department || filters.location || filters.role) {
        filtered = filtered.filter(absence => {
          const employee = employees.find(emp => emp.id === absence.employeeId);
          if (!employee) return false;
          
          if (filters.department && employee.department !== filters.department) return false;
          if (filters.location && employee.location !== filters.location) return false;
          if (filters.role && employee.role !== filters.role) return false;
          
          return true;
        });
      }
      
      return filtered;
    };

    // Generate search suggestions based on available data
    const generateSuggestions = (employees, query) => {
      if (!query.trim() || !employees || employees.length === 0) return [];
      
      const searchTerm = query.toLowerCase().trim();
      const suggestions = new Set();
      
      employees.forEach(employee => {
        // Add matching names
        if (employee.name?.toLowerCase().includes(searchTerm)) {
          suggestions.add(employee.name);
        }
        
        // Add matching departments
        if (employee.department?.toLowerCase().includes(searchTerm)) {
          suggestions.add(employee.department);
        }
        
        // Add matching roles
        if (employee.role?.toLowerCase().includes(searchTerm)) {
          suggestions.add(employee.role);
        }
        
        // Add matching locations
        if (employee.location?.toLowerCase().includes(searchTerm)) {
          suggestions.add(employee.location);
        }
      });
      
      return Array.from(suggestions).slice(0, 5); // Limit to 5 suggestions
    };

    return { searchEmployees, searchAbsences, generateSuggestions };
  }, []);

  // Perform search with memoized operations
  const performSearch = useCallback((employees, absences, query, filters, searchType) => {
    dispatch({ type: 'SEARCH_START' });
    
    try {
      let results = { employees: [], absences: [] };
      
      if (searchType === 'all' || searchType === 'employees') {
        results.employees = searchOperations.searchEmployees(employees, query, filters);
      }
      
      if (searchType === 'all' || searchType === 'absences') {
        results.absences = searchOperations.searchAbsences(absences, employees, query, filters);
      }
      
      dispatch({ type: 'SEARCH_SUCCESS', payload: results });
      
      // Generate suggestions for future searches
      const suggestions = searchOperations.generateSuggestions(employees, query);
      dispatch({ type: 'SET_SUGGESTIONS', payload: suggestions });
      
    } catch (error) {
      console.error('Search error:', error);
      dispatch({ type: 'SEARCH_ERROR' });
    }
  }, [searchOperations]);

  // Set search query
  const setQuery = useCallback((query) => {
    dispatch({ type: 'SET_QUERY', payload: query });
  }, []);

  // Set search filter
  const setFilter = useCallback((key, value) => {
    dispatch({ type: 'SET_FILTER', payload: { key, value } });
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    dispatch({ type: 'CLEAR_FILTERS' });
  }, []);

  // Set active search type
  const setSearchType = useCallback((searchType) => {
    dispatch({ type: 'SET_SEARCH_TYPE', payload: searchType });
  }, []);

  // Clear search
  const clearSearch = useCallback(() => {
    dispatch({ type: 'CLEAR_SEARCH' });
  }, []);

  // Clear search history
  const clearSearchHistory = useCallback(() => {
    dispatch({ type: 'CLEAR_SEARCH_HISTORY' });
  }, []);

  // Memoized dispatch actions
  const dispatchActions = useMemo(() => ({
    performSearch,
    setQuery,
    setFilter,
    clearFilters,
    setSearchType,
    clearSearch,
    clearSearchHistory,
    dispatch
  }), [
    performSearch,
    setQuery,
    setFilter,
    clearFilters,
    setSearchType,
    clearSearch,
    clearSearchHistory
  ]);

  return (
    <SearchMemoryStateContext.Provider value={state}>
      <SearchMemoryDispatchContext.Provider value={dispatchActions}>
        {children}
      </SearchMemoryDispatchContext.Provider>
    </SearchMemoryStateContext.Provider>
  );
}

// Hook to access search state
export function useSearchMemoryState() {
  const context = useContext(SearchMemoryStateContext);
  if (!context) {
    throw new Error('useSearchMemoryState must be used within SearchMemoryProvider');
  }
  return context;
}

// Hook to access search dispatch functions
export function useSearchMemoryDispatch() {
  const context = useContext(SearchMemoryDispatchContext);
  if (!context) {
    throw new Error('useSearchMemoryDispatch must be used within SearchMemoryProvider');
  }
  return context;
}

// Action creators for common search operations
export const searchActions = {
  setQuery: (query) => ({ type: 'SET_QUERY', payload: query }),
  setFilter: (key, value) => ({ type: 'SET_FILTER', payload: { key, value } }),
  clearFilters: () => ({ type: 'CLEAR_FILTERS' }),
  setSearchType: (searchType) => ({ type: 'SET_SEARCH_TYPE', payload: searchType }),
  clearSearch: () => ({ type: 'CLEAR_SEARCH' }),
  clearSearchHistory: () => ({ type: 'CLEAR_SEARCH_HISTORY' }),
};




// purpose To manage the state of the search functionality
//query: The exact text the user has typed into the search bar at the top of the page.
//filters: Any advanced filters the user has selected, like filtering by a specific department on a dedicated search page
//results: A folder containing the list of employees or absences that matched the last search the user ran.
//searchHistory: A short list of the user's most recent search terms
