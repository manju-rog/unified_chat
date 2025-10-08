import { useState, useMemo, useCallback } from 'react';

export function useEmployeeFilters(employees, query, departments, locations) {
  const [selectedDepartment, setSelectedDepartment] = useState('All Departments');
  const [selectedLocation, setSelectedLocation] = useState('All Locations');

  // Memoized employee filtering function
  const filteredEmployees = useMemo(() => {
    if (!employees || employees.length === 0) {
      return [];
    }

    return employees.filter(employee => {
      // Search query filter - matches name or email
      const matchesSearch = !query || 
                           employee.name?.toLowerCase().includes(query.toLowerCase()) ||
                           employee.email?.toLowerCase().includes(query.toLowerCase());
      
      // Department filter
      const matchesDepartment = selectedDepartment === 'All Departments' || 
                               employee.department === selectedDepartment;
      
      // Location filter
      const matchesLocation = selectedLocation === 'All Locations' || 
                             employee.location === selectedLocation;
      
      return matchesSearch && matchesDepartment && matchesLocation;
    });
  }, [employees, query, selectedDepartment, selectedLocation]);

  const handleDepartmentChange = useCallback((department) => {
    setSelectedDepartment(department);
  }, []);

  const handleLocationChange = useCallback((location) => {
    setSelectedLocation(location);
  }, []);

  return {
    selectedDepartment,
    selectedLocation,
    filteredEmployees,
    handleDepartmentChange,
    handleLocationChange
  };
}