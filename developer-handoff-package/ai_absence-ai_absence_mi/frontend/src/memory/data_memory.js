import React, { createContext, useContext, useReducer, useEffect, useMemo, useCallback } from 'react';
import { seedData } from '../initial_data/seed_data';
import api from '../services/api';

// Context for data state and dispatch
const DataMemoryStateContext = createContext();
const DataMemoryDispatchContext = createContext();

// Initial data state
const initialState = {
  employees: [],
  absenceRecords: [],
  absenceData: {},
  selectedMonth: '2024-06',
  departments: seedData.departments,
  locations: seedData.locations,
  roles: seedData.roles,
  absenceTypes: seedData.absenceTypes,

  // Action Bus for AI commands
  pendingCommand: null,

  loading: {
    employees: false,
    absences: false,
    dashboard: false,
  },
  errors: {
    employees: null,
    absences: null,
    dashboard: null,
  }
};

// Data reducer for handling data-related state changes
function dataReducer(state, action) {
  switch (action.type) {
    case 'SET_MONTH':
      return { ...state, selectedMonth: action.payload };
    
    case 'UPDATE_ABSENCE_DATA':
      return {
        ...state,
        absenceData: { ...state.absenceData, ...action.payload }
      };
    
    case 'LOAD_EMPLOYEES_START':
      return { 
        ...state, 
        loading: { ...state.loading, employees: true },
        errors: { ...state.errors, employees: null }
      };
    
    case 'LOAD_EMPLOYEES_SUCCESS':
      return { 
        ...state, 
        employees: action.payload,
        loading: { ...state.loading, employees: false }
      };
    
    case 'LOAD_EMPLOYEES_ERROR':
      return { 
        ...state, 
        loading: { ...state.loading, employees: false },
        errors: { ...state.errors, employees: action.payload }
      };
    
    case 'ADD_EMPLOYEE_SUCCESS':
      const updatedEmployees = [...state.employees, action.payload];
      return {
        ...state,
        employees: updatedEmployees
      };
    
    case 'LOAD_ABSENCES_START':
      return { 
        ...state, 
        loading: { ...state.loading, absences: true },
        errors: { ...state.errors, absences: null }
      };
    
    case 'LOAD_ABSENCES_SUCCESS':
      return { 
        ...state, 
        absenceRecords: action.payload,
        loading: { ...state.loading, absences: false }
      };
    
    case 'LOAD_ABSENCES_ERROR':
      return { 
        ...state, 
        loading: { ...state.loading, absences: false },
        errors: { ...state.errors, absences: action.payload }
      };
    
    case 'SET_PENDING_COMMAND':
      return {
        ...state,
        pendingCommand: action.payload
      };
    
    case 'CLEAR_PENDING_COMMAND':
      return {
        ...state,
        pendingCommand: null
      };
    
    default:
      return state;
  }
}

// Data memory provider component
export function DataMemoryProvider({ children }) {
  const [state, dispatch] = useReducer(dataReducer, initialState);

  const loadEmployees = useCallback(async () => {
    dispatch({ type: 'LOAD_EMPLOYEES_START' });
    try {
      const employees = await api.employees.getAll();
      dispatch({ type: 'LOAD_EMPLOYEES_SUCCESS', payload: employees });
      
      const allAbsenceRecords = employees.flatMap(employee => 
        (employee.absenceRecords || []).map(record => ({
          ...record,
          employeeId: employee.id,
          employeeName: employee.name
        }))
      );
      dispatch({ type: 'LOAD_ABSENCES_SUCCESS', payload: allAbsenceRecords });
    } catch (error) {
      console.error('Failed to load employees:', error);
      dispatch({ type: 'LOAD_EMPLOYEES_ERROR', payload: api.utils.handleError(error) });
    }
  }, []);

  const loadAbsences = useCallback(async () => {
    console.log('Absences are loaded as part of employee data');
  }, []);

  useEffect(() => {
    loadEmployees();
  }, [loadEmployees]);

  const addEmployee = useCallback((employee) => {
    dispatch({ type: 'ADD_EMPLOYEE_SUCCESS', payload: employee });
  }, []);

  const updateAbsenceData = useCallback((data) => {
    dispatch({ type: 'UPDATE_ABSENCE_DATA', payload: data });
  }, []);

  const setSelectedMonth = useCallback((month) => {
    dispatch({ type: 'SET_MONTH', payload: month });
  }, []);

  const executeCommand = useCallback((command) => {
    dispatch({ type: 'SET_PENDING_COMMAND', payload: command });
  }, []);

  const clearCommand = useCallback(() => {
    dispatch({ type: 'CLEAR_PENDING_COMMAND' });
  }, []);

  const refreshData = useCallback(async () => {
    await loadEmployees();
  }, [loadEmployees]);

  const dispatchActions = useMemo(() => ({
    loadEmployees,
    loadAbsences,
    addEmployee,
    updateAbsenceData,
    setSelectedMonth,
    executeCommand,
    clearCommand,
    refreshData,
    dispatch
  }), [loadEmployees, loadAbsences, addEmployee, updateAbsenceData, setSelectedMonth, executeCommand, clearCommand, refreshData]);

  return (
    <DataMemoryStateContext.Provider value={state}>
      <DataMemoryDispatchContext.Provider value={dispatchActions}>
        {children}
      </DataMemoryDispatchContext.Provider>
    </DataMemoryStateContext.Provider>
  );
}

// Hook to access data state
export function useDataMemoryState() {
  const context = useContext(DataMemoryStateContext);
  if (!context) {
    throw new Error('useDataMemoryState must be used within DataMemoryProvider');
  }
  return context;
}

// Hook to access data dispatch functions
export function useDataMemoryDispatch() {
  const context = useContext(DataMemoryDispatchContext);
  if (!context) {
    throw new Error('useDataMemoryDispatch must be used within DataMemoryProvider');
  }
  return context;
}

