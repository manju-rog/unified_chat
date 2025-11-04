// Header row: day numbers
import React from 'react';
import '../../../css_design/components/Views/AbsenceGrid.css';

const GridHeaderRow = React.memo(({ days, selectedYear, selectedMonthIndex }) => {
  return (
    <div className="grid-header">
      <div className="employee-header">
        Employee
      </div>
      {days.map(({ day, dayName, isToday }) => (
        <div 
          key={day} 
          className={`day-header ${isToday ? 'today' : ''}`}
        >
          <div className="day-number">{day}</div>
          <div className="day-name">{dayName}</div>
        </div>
      ))}
    </div>
  );
});

GridHeaderRow.displayName = 'GridHeaderRow';

export default GridHeaderRow;