import React from 'react';
import './DayDetailModal.css';

const DayDetailModal = ({ dayData, isOpen, onClose, position }) => {
  if (!isOpen || !dayData) return null;

  const { date, dayOfWeek, employees, holiday, statistics, department } = dayData;
  const { totalEmployees, absent, vacation, present, departmentBreakdown } = statistics;

  // Format date for display
  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'A': return '#ef4444';
      case 'V': return '#8b5cf6';
      case 'P': return '#10b981';
      default: return '#6b7280';
    }
  };

  // Get status label
  const getStatusLabel = (status) => {
    switch (status) {
      case 'A': return 'Absent';
      case 'V': return 'Vacation';
      case 'P': return 'Present';
      default: return 'Unknown';
    }
  };

  return (
    <div className="day-modal-overlay" onClick={onClose}>
      <div 
        className="day-modal" 
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="day-modal-header">
          <div className="day-modal-title">
            <h3>{formatDate(date)}</h3>
            {holiday && (
              <div className="holiday-badge">
                🎉 {holiday.name}
              </div>
            )}
          </div>
          <button className="day-modal-close" onClick={onClose}>×</button>
        </div>

        {/* Statistics Overview */}
        <div className="day-modal-stats">
          <div className="stat-card stat-total">
            <div className="stat-number">{totalEmployees}</div>
            <div className="stat-label">Total Employees</div>
          </div>
          <div className="stat-card stat-present">
            <div className="stat-number">{present}</div>
            <div className="stat-label">Present</div>
          </div>
          <div className="stat-card stat-absent">
            <div className="stat-number">{absent}</div>
            <div className="stat-label">Absent</div>
          </div>
          <div className="stat-card stat-vacation">
            <div className="stat-number">{vacation}</div>
            <div className="stat-label">Vacation</div>
          </div>
        </div>

        {/* Department Breakdown (if showing all departments) */}
        {!department && departmentBreakdown && Object.keys(departmentBreakdown).length > 1 && (
          <div className="day-modal-section">
            <h4>Department Breakdown</h4>
            <div className="dept-breakdown">
              {Object.entries(departmentBreakdown).map(([dept, stats]) => (
                <div key={dept} className="dept-card">
                  <div className="dept-name">{dept}</div>
                  <div className="dept-stats">
                    {Object.entries(stats).map(([status, count]) => (
                      <span 
                        key={status} 
                        className="dept-stat"
                        style={{ color: getStatusColor(status) }}
                      >
                        {status}: {count}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Employee Lists */}
        <div className="day-modal-content">
          {['A', 'V', 'P'].map(status => {
            const employeeList = employees[status] || [];
            if (employeeList.length === 0) return null;

            return (
              <div key={status} className="employee-section">
                <h4 className="section-title" style={{ color: getStatusColor(status) }}>
                  {getStatusLabel(status)} ({employeeList.length})
                </h4>
                <div className="employee-list">
                  {employeeList.map(emp => (
                    <div key={emp.id} className="employee-card">
                      <div className="employee-info">
                        <div className="employee-name">{emp.name}</div>
                        <div className="employee-details">
                          <span className="employee-email">{emp.email}</span>
                          <span className="employee-dept">{emp.department}</span>
                        </div>
                        {emp.reason && (
                          <div className="employee-reason">
                            <em>"{emp.reason}"</em>
                          </div>
                        )}
                      </div>
                      <div 
                        className="status-indicator"
                        style={{ backgroundColor: getStatusColor(status) }}
                      >
                        {status}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Holiday Details */}
        {holiday && (
          <div className="day-modal-section holiday-section">
            <h4>🎉 Public Holiday</h4>
            <div className="holiday-details">
              <div className="holiday-name">{holiday.name}</div>
              <div className="holiday-info">
                <span>Country: {holiday.countryCode}</span>
                {holiday.region && <span>Region: {holiday.region}</span>}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DayDetailModal;