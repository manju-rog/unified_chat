// Month & year selector (super clear)
import React from 'react';
import '../../../css_design/components/Views/AbsenceGridFilters.css';

const MonthSelector = React.memo(({
  selectedYear,
  selectedMonthIndex,
  isDatePickerOpen,
  isCurrentMonth,
  getFormattedDate,
  onOpenDatePicker,
  onCloseDatePicker,
  onYearChange,
  onMonthChange,
  onPreviousMonth,
  onNextMonth,
  onCurrentMonth
}) => {
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const monthShortNames = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];

  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();
  const currentMonthIndex = currentDate.getMonth();

  // Generate year options (current year ± 5 years)
  const yearOptions = [];
  for (let year = currentYear - 5; year <= currentYear + 5; year++) {
    yearOptions.push(year);
  }

  return (
    <div className="date-picker-group">
      <div className="date-picker-container">
        <button
          className="date-nav-btn"
          onClick={onPreviousMonth}
          title="Previous month"
        >
          <span className="material-icons">chevron_left</span>
        </button>
        
        <div className="date-picker-main">
          <button
            className={`date-display-btn ${isCurrentMonth ? 'current-month' : ''}`}
            onClick={onOpenDatePicker}
          >
            <span className="date-text">{getFormattedDate()}</span>
            <span className="material-icons">expand_more</span>
          </button>
          
          {isDatePickerOpen && (
            <div className="date-picker-dropdown">
              <div className="date-picker-header">
                <h4>Select Month & Year</h4>
                <button className="close-picker" onClick={onCloseDatePicker}>
                  <span className="material-icons">close</span>
                </button>
              </div>
              
              <div className="year-selection">
                <label>Year:</label>
                <select
                  className="year-select"
                  value={selectedYear}
                  onChange={(e) => onYearChange(e.target.value)}
                >
                  {yearOptions.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>
              
              <div className="month-grid">
                {monthNames.map((month, index) => (
                  <button
                    key={index}
                    className={`month-btn ${
                      index === selectedMonthIndex ? 'selected' : ''
                    } ${
                      index === currentMonthIndex && selectedYear === currentYear ? 'current' : ''
                    }`}
                    onClick={() => onMonthChange(index)}
                  >
                    <span className="month-name">{month}</span>
                    <span className="month-short">{monthShortNames[index]}</span>
                  </button>
                ))}
              </div>
              
              <div className="date-picker-actions">
                <button
                  className="glass-btn glass-btn--secondary current-month-btn"
                  onClick={onCurrentMonth}
                >
                  <span className="material-icons">today</span>
                  Current Month
                  <div className="btn-glow"></div>
                </button>
              </div>
            </div>
          )}
        </div>
        
        <button
          className="date-nav-btn"
          onClick={onNextMonth}
          title="Next month"
        >
          <span className="material-icons">chevron_right</span>
        </button>
      </div>
      
      {isCurrentMonth && (
        <div className="current-month-indicator">
          <span className="material-icons">today</span>
          Current Month
        </div>
      )}
    </div>
  );
});

MonthSelector.displayName = 'MonthSelector';

export default MonthSelector;