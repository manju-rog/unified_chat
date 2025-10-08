// Main Employees page
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDataMemoryState } from '../../memory/data_memory';
import { useSearchMemoryState } from '../../memory/search_memory';

// Import modular components
import TopArea from './parts/TopArea';
import EmployeesTable from './parts/EmployeesTable';
import AddEmployeeBox from './parts/AddEmployeeBox';

// Import utilities and hooks
import { useEmployeeSelection } from '../../hooks/useEmployeeSelection';
import { useEmployeeFilters } from '../../hooks/useEmployeeFilters';
import { useEmployeeActions } from './work/add_employee';

// Import styles
import '../../css_design/components/Views/EmployeeManagement.css';

function EmployeesPage() {
  const { employees, departments, locations } = useDataMemoryState();
  const { query } = useSearchMemoryState();
  const location = useLocation();
  const navigate = useNavigate();

  // Employee selection hook
  const {
    selectedEmployees,
    handleEmployeeSelect,
    handleSelectAll,
    isAllSelected
  } = useEmployeeSelection();

  // Employee filters hook
  const {
    selectedDepartment,
    selectedLocation,
    filteredEmployees,
    handleDepartmentChange,
    handleLocationChange
  } = useEmployeeFilters(employees, query, departments, locations);

  // Employee actions hook
  const {
    isAddModalOpen,
    handleAddModalOpen,
    handleAddModalClose,
    handleAddEmployeeSuccess,
    handleImportCSV,
    handleExport,
    handleDeleteSelected,
    handleExportSelected
  } = useEmployeeActions(location, navigate, selectedEmployees);

  return (
    <div className="employee-management-clean">
      {/* Clean background */}
      <div className="clean-background"></div>
      
      {/* Header */}
      <div className="view__header">
        <div className="view__title">
          <h1>Employee Management</h1>
          <p>Manage employee information and details</p>
        </div>
        <TopArea 
          onAddEmployee={handleAddModalOpen}
          onImportCSV={handleImportCSV}
          onExport={handleExport}
        />
      </div>
      
      {/* Table */}
      <EmployeesTable
        employees={filteredEmployees}
        selectedEmployees={selectedEmployees}
        isAllSelected={isAllSelected}
        onEmployeeSelect={handleEmployeeSelect}
        onSelectAll={handleSelectAll}
        query={query}
        filteredEmployeesCount={filteredEmployees.length}
        selectedDepartment={selectedDepartment}
        selectedLocation={selectedLocation}
        departments={departments}
        locations={locations}
        onDepartmentChange={handleDepartmentChange}
        onLocationChange={handleLocationChange}
        totalEmployees={employees.length}
        selectedEmployeesCount={selectedEmployees.length}
        onDeleteSelected={handleDeleteSelected}
        onExportSelected={handleExportSelected}
      />
      
      {/* Add Employee Modal */}
      <AddEmployeeBox
        isOpen={isAddModalOpen}
        onClose={handleAddModalClose}
        onSuccess={handleAddEmployeeSuccess}
      />
    </div>
  );
}

export default React.memo(EmployeesPage);