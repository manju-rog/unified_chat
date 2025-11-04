// One day cell: cycles P → A → V
import React from 'react';
import { makeKey } from '../save_and_changes/make_key';
import '../../../css_design/components/Views/AbsenceGridCells.css';

const OneDayCell = React.memo(({
  employeeId,
  day,
  isoString,
  absenceData,
  absenceTypes,
  editingCell,
  onCellClick,
  onStatusChange,
  onCancelEdit
}) => {
  const cellKey = makeKey(employeeId, isoString);
  const status = absenceData[cellKey] || 'P'; // Default to Present
  const isEditing = editingCell === cellKey;
  
  // Get status info
  const statusInfo = absenceTypes[status] || absenceTypes['P'];
  
  // Cycle through statuses: P → A → V → P
  const getNextStatus = (currentStatus) => {
    const statusOrder = ['P', 'A', 'V'];
    const currentIndex = statusOrder.indexOf(currentStatus);
    const nextIndex = (currentIndex + 1) % statusOrder.length;
    return statusOrder[nextIndex];
  };

  const handleCellClick = () => {
    if (!isEditing) {
      const nextStatus = getNextStatus(status);
      onStatusChange(cellKey, nextStatus, employeeId, isoString);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleCellClick();
    } else if (e.key === 'Escape') {
      onCancelEdit();
    }
  };

  // Get CSS class based on status
  const getCellClass = () => {
    let baseClass = 'absence-cell';
    
    switch (status) {
      case 'P':
        baseClass += ' absence-cell--present';
        break;
      case 'A':
        baseClass += ' absence-cell--absent';
        break;
      case 'V':
        baseClass += ' absence-cell--vacation';
        break;
      default:
        baseClass += ' absence-cell--present';
    }
    
    if (isEditing) {
      baseClass += ' absence-cell--editing';
    }
    
    return baseClass;
  };

  return (
    <div
      className={getCellClass()}
      onClick={handleCellClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`${statusInfo.label} for day ${day}`}
      title={`Click to change status (currently: ${statusInfo.label})`}
    >
      {status}
    </div>
  );
});

OneDayCell.displayName = 'OneDayCell';

export default OneDayCell;