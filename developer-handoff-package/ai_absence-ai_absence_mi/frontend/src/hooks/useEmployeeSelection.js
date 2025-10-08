import { useState, useCallback, useMemo } from 'react';

export function useEmployeeSelection() {
  const [selectedEmployees, setSelectedEmployees] = useState([]);

  const handleEmployeeSelect = useCallback((employeeId) => {
    setSelectedEmployees(prev => {
      if (prev.includes(employeeId)) {
        return prev.filter(id => id !== employeeId);
      } else {
        return [...prev, employeeId];
      }
    });
  }, []);

  const handleSelectAll = useCallback((employees) => {
    setSelectedEmployees(prev => {
      if (prev.length === employees.length) {
        return []; // Deselect all
      } else {
        return employees.map(emp => emp.id); // Select all
      }
    });
  }, []);

  const isAllSelected = useMemo(() => {
    return selectedEmployees.length > 0;
  }, [selectedEmployees.length]);

  return {
    selectedEmployees,
    handleEmployeeSelect,
    handleSelectAll,
    isAllSelected
  };
}