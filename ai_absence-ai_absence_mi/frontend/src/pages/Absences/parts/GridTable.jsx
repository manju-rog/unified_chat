// The table shell
import React from 'react';
import GridHeaderRow from './GridHeaderRow';
import OneEmployeeRow from './OneEmployeeRow';
import '../../../css_design/components/Views/AbsenceGrid.css';

const GridTable = React.memo(({
  employees,
  days,
  selectedYear,
  selectedMonthIndex,
  absenceData,
  absenceTypes,
  editingCell,
  onCellClick,
  onStatusChange,
  onCancelEdit
}) => {
  return (
    <div className="absence-grid-container">
      <div className="absence-grid">
        <GridHeaderRow
          days={days}
          selectedYear={selectedYear}
          selectedMonthIndex={selectedMonthIndex}
        />
        {employees.map((employee) => (
          <OneEmployeeRow
            key={employee.id}
            employee={employee}
            days={days}
            absenceData={absenceData}
            absenceTypes={absenceTypes}
            editingCell={editingCell}
            onCellClick={onCellClick}
            onStatusChange={onStatusChange}
            onCancelEdit={onCancelEdit}
          />
        ))}
      </div>
    </div>
  );
});

GridTable.displayName = 'GridTable';

export default GridTable;