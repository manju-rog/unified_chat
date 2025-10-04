import React from 'react';
import './AbsenceQueryPopup.css';

const AbsenceQueryPopup = React.memo(({ 
  isVisible, 
  onClose, 
  queryResults, 
  queryDate, 
  queryType,
  displayPeriod,
  totalEmployees = 5 // Default fallback
}) => {
  if (!isVisible || !queryResults) return null;

  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long',
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  // Format date for short display (e.g., "Aug 14")
  const formatDateShort = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  // Get status display info
  const getStatusInfo = (status) => {
    switch (status) {
      case 'A':
        return { label: 'Absent', icon: 'cancel', color: '#ef4444' };
      case 'V':
        return { label: 'Vacation', icon: 'beach_access', color: '#3b82f6' };
      case 'P':
        return { label: 'Present', icon: 'check_circle', color: '#10b981' };
      default:
        return { label: 'Unknown', icon: 'help', color: '#6b7280' };
    }
  };

  // Group results by status, then by employee
  const groupedResults = queryResults.reduce((acc, result) => {
    if (!acc[result.status]) {
      acc[result.status] = {};
    }
    
    const employeeKey = `${result.employeeName}-${result.employeeId}`;
    if (!acc[result.status][employeeKey]) {
      acc[result.status][employeeKey] = {
        employeeName: result.employeeName,
        employeeId: result.employeeId,
        department: result.department,
        dates: []
      };
    }
    
    acc[result.status][employeeKey].dates.push(result.date);
    return acc;
  }, {});

  const totalCount = queryResults.length;
  const absentCount = groupedResults['A'] ? Object.keys(groupedResults['A']).length : 0;
  const vacationCount = groupedResults['V'] ? Object.keys(groupedResults['V']).length : 0;
  const presentCount = groupedResults['P'] ? Object.keys(groupedResults['P']).length : 0;
  const uniqueEmployeeCount = absentCount + vacationCount + presentCount;

  return (
    <div className="absence-query-overlay" onClick={onClose}>
      <div className="absence-query-popup" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="popup-header">
          <div className="popup-title">
            <span className="material-icons">
              {presentCount > 0 ? 'event_available' : 'event_busy'}
            </span>
            <h3>
              {presentCount > 0 && (absentCount === 0 && vacationCount === 0) 
                ? 'Attendance Report' 
                : 'Absence Report'}
            </h3>
          </div>
          <button className="popup-close-btn" onClick={onClose}>
            <span className="material-icons">close</span>
          </button>
        </div>

        {/* Date Info */}
        <div className="popup-date-info">
          <span className="material-icons">calendar_today</span>
          <span className="date-text">
            {displayPeriod || formatDate(queryDate)}
          </span>
        </div>

        {/* Summary Stats */}
        <div className="popup-summary">
          <div className="summary-text">
            {presentCount > 0 && absentCount === 0 && vacationCount === 0 ? (
              <span className="summary-main">
                <strong>{presentCount}</strong> {presentCount === 1 ? 'employee is' : 'employees are'} present
              </span>
            ) : absentCount > 0 && presentCount === 0 && vacationCount === 0 ? (
              <span className="summary-main">
                <strong>{absentCount}</strong> {absentCount === 1 ? 'employee is' : 'employees are'} absent
              </span>
            ) : vacationCount > 0 && presentCount === 0 && absentCount === 0 ? (
              <span className="summary-main">
                <strong>{vacationCount}</strong> {vacationCount === 1 ? 'employee is' : 'employees are'} on vacation
              </span>
            ) : absentCount > 0 || vacationCount > 0 ? (
              <span className="summary-main">
                <strong>{absentCount + vacationCount}</strong> employees are away
                {presentCount > 0 && (
                  <span className="summary-sub">
                    • {presentCount} present
                  </span>
                )}
              </span>
            ) : (
              <span className="summary-main">No attendance data found</span>
            )}
          </div>
          
          {(presentCount > 0 || absentCount > 0 || vacationCount > 0) && totalEmployees && (
            <div className="attendance-bar">
              <div className="bar-container">
                {/* Show full context bar when we have total employees count */}
                {presentCount > 0 && (
                  <div 
                    className="bar-segment present-bar" 
                    style={{ width: `${(presentCount / totalEmployees) * 100}%` }}
                    title={`${presentCount} Present`}
                  />
                )}
                {absentCount > 0 && (
                  <div 
                    className="bar-segment absent-bar" 
                    style={{ width: `${(absentCount / totalEmployees) * 100}%` }}
                    title={`${absentCount} Absent`}
                  />
                )}
                {vacationCount > 0 && (
                  <div 
                    className="bar-segment vacation-bar" 
                    style={{ width: `${(vacationCount / totalEmployees) * 100}%` }}
                    title={`${vacationCount} Vacation`}
                  />
                )}
                {/* Show remaining employees as a light gray segment if not all are accounted for */}
                {(presentCount + absentCount + vacationCount) < totalEmployees && (
                  <div 
                    className="bar-segment unknown-bar" 
                    style={{ width: `${((totalEmployees - presentCount - absentCount - vacationCount) / totalEmployees) * 100}%` }}
                    title={`${totalEmployees - presentCount - absentCount - vacationCount} No Data`}
                  />
                )}
              </div>
              <div className="bar-legend">
                {presentCount > 0 && (
                  <span className="legend-item present">
                    <span className="legend-dot"></span>
                    Present ({presentCount})
                  </span>
                )}
                {absentCount > 0 && (
                  <span className="legend-item absent">
                    <span className="legend-dot"></span>
                    Absent ({absentCount})
                  </span>
                )}
                {vacationCount > 0 && (
                  <span className="legend-item vacation">
                    <span className="legend-dot"></span>
                    Vacation ({vacationCount})
                  </span>
                )}
                {(presentCount + absentCount + vacationCount) < totalEmployees && (
                  <span className="legend-item unknown">
                    <span className="legend-dot"></span>
                    No Data ({totalEmployees - presentCount - absentCount - vacationCount})
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Results List */}
        <div className="popup-content">
          {totalCount === 0 ? (
            <div className="no-results">
              <span className="material-icons">sentiment_satisfied</span>
              <h4>Great news! 🎉</h4>
              <p>No records found for {displayPeriod || formatDate(queryDate)}. This could mean everyone was present or no data is available for this period.</p>
            </div>
          ) : (
            <div className="results-list">
              {Object.entries(groupedResults).map(([status, employeesObj]) => {
                const statusInfo = getStatusInfo(status);
                const employees = Object.values(employeesObj);
                return (
                  <div key={status} className="status-group">
                    <div className="status-header">
                      <span 
                        className="material-icons" 
                        style={{ color: statusInfo.color }}
                      >
                        {statusInfo.icon}
                      </span>
                      <h4 style={{ color: statusInfo.color }}>
                        {statusInfo.label} ({employees.length})
                      </h4>
                    </div>
                    <div className="employee-list">
                      {employees.map((employee, index) => (
                        <div key={index} className="employee-item">
                          <div className="employee-avatar">
                            {employee.employeeName.charAt(0).toUpperCase()}
                          </div>
                          <div className="employee-info">
                            <span className="employee-name">{employee.employeeName}</span>
                            <span className="employee-department">{employee.department || 'Unknown Dept'}</span>
                          </div>
                          <div className="employee-dates">
                            <span className="material-icons">calendar_today</span>
                            <div className="dates-list">
                              {employee.dates.sort().map((date, dateIndex) => (
                                <span key={dateIndex} className="date-badge">
                                  {formatDateShort(date)}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="popup-footer">
          <button className="popup-action-btn" onClick={onClose}>
            <span className="material-icons">check</span>
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
});

AbsenceQueryPopup.displayName = 'AbsenceQueryPopup';

export default AbsenceQueryPopup;