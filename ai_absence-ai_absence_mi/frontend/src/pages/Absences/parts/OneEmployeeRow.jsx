// One row for one employee
import React from 'react';
import OneDayCell from './OneDayCell';
import '../../../css_design/components/Views/AbsenceGrid.css';

const OneEmployeeRow = React.memo(({
  employee,
  days,
  absenceData,
  absenceTypes,
  editingCell,
  onCellClick,
  onStatusChange,
  onCancelEdit
}) => {
  return (
    <div className="employee-row">
      <div className="employee-info">
        <div className="employee-name">{employee.name}</div>
        <div className="employee-dept">{employee.department}</div>
      </div>
      
      {days.map(({ day, isoString }) => (
        <OneDayCell
          key={`${employee.id}-${day}`}
          employeeId={employee.id}
          day={day}
          isoString={isoString}
          absenceData={absenceData}
          absenceTypes={absenceTypes}
          editingCell={editingCell}
          onCellClick={onCellClick}
          onStatusChange={onStatusChange}
          onCancelEdit={onCancelEdit}
        />
      ))}
    </div>
  );
});

OneEmployeeRow.displayName = 'OneEmployeeRow';

export default OneEmployeeRow;