// Table shell for employees
import React from 'react';
import OneEmployeeRow from './OneEmployeeRow';

const EmployeesTable = React.memo(({
  employees,
  selectedEmployees,
  isAllSelected,
  onEmployeeSelect,
  onSelectAll,
  query,
  filteredEmployeesCount,
  selectedDepartment,
  selectedLocation,
  departments,
  locations,
  onDepartmentChange,
  onLocationChange,
  totalEmployees,
  selectedEmployeesCount,
  onDeleteSelected,
  onExportSelected
}) => {
  return (
    <>
      {/* Filters */}
      <div className="employee-filters">
        <div className="filter-section">
          <select
            className="filter-dropdown"
            value={selectedDepartment}
            onChange={(e) => onDepartmentChange(e.target.value)}
          >
            <option value="All Departments">All Departments</option>
            {departments.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
          
          <select
            className="filter-dropdown"
            value={selectedLocation}
            onChange={(e) => onLocationChange(e.target.value)}
          >
            <option value="All Locations">All Locations</option>
            {locations.map(location => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </div>
        
        <div className="filter-section">
          {query && (
            <div className="search-status">
              <span className="material-icons">search</span>
              Searching for "{query}" - {filteredEmployeesCount} results
            </div>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="employee-table-container">
        <div className="employee-table-wrapper">
          <table className="employee-table">
            <thead>
              <tr>
                <th className="checkbox-column">
                  <input
                    type="checkbox"
                    className="table-checkbox"
                    checked={isAllSelected}
                    onChange={onSelectAll}
                  />
                </th>
                <th className="name-column">NAME</th>
                <th className="email-column">EMAIL</th>
                <th className="department-column">DEPARTMENT</th>
                <th className="role-column">ROLE</th>
                <th className="location-column">LOCATION</th>
                <th className="system-column">SYSTEM</th>
                <th className="actions-column">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((employee) => (
                <OneEmployeeRow
                  key={employee.id}
                  employee={employee}
                  isSelected={selectedEmployees.includes(employee.id)}
                  onSelect={() => onEmployeeSelect(employee.id)}
                />
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Footer */}
        <div className="table-footer">
          <div className="results-info">
            Showing {filteredEmployeesCount} of {totalEmployees} employees
            {selectedEmployeesCount > 0 && (
              <span className="selection-info">
                ({selectedEmployeesCount} selected)
              </span>
            )}
          </div>
          
          {selectedEmployeesCount > 0 && (
            <div className="bulk-actions">
              <button
                className="glass-btn glass-btn--secondary"
                onClick={onExportSelected}
              >
                Export Selected
                <div className="btn-glow"></div>
              </button>
              <button
                className="glass-btn glass-btn--danger"
                onClick={onDeleteSelected}
              >
                Delete Selected
                <div className="btn-glow"></div>
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
});

EmployeesTable.displayName = 'EmployeesTable';

export default EmployeesTable;