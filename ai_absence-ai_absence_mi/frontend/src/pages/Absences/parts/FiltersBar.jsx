// Department + text filter component
import React from 'react';
import { useDataMemoryState } from '../../../memory/data_memory';
import MonthSelector from './MonthSelector';
import '../../../css_design/components/Views/AbsenceGridFilters.css';

const FiltersBar = React.memo(({ 
  selectedDepartment, 
  onDepartmentChange, 
  onClearFilters,
  datePickerProps 
}) => {
  const { departments } = useDataMemoryState();

  return (
    <div className="grid-filters">
      <div className="grid-filters-left">
        <div className="filter-group">
          <label>Department:</label>
          <select
            className="filter-select"
            value={selectedDepartment}
            onChange={(e) => onDepartmentChange(e.target.value)}
          >
            <option value="All Departments">All Departments</option>
            {departments.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        </div>
        
        <MonthSelector {...datePickerProps} />
      </div>
      
      <div className="grid-filters-right">
        <button
          className="clear-filters-btn"
          onClick={onClearFilters}
          title="Clear all filters"
        >
          <span className="material-icons">clear_all</span>
          Clear Filters
        </button>
      </div>
    </div>
  );
});

FiltersBar.displayName = 'FiltersBar';

export default FiltersBar;