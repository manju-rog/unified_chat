// Main AbsencesPage component - short and clean
import React, { useEffect, useMemo } from 'react';
import { useDataMemoryState, useDataMemoryDispatch } from '../../memory/data_memory';
import { useSearchMemoryState } from '../../memory/search_memory';
import { useAppMemory } from '../../memory/app_memory';
import { useChatbotMemoryDispatch } from '../../memory/chatbot_memory';

// Import modular components
import FiltersBar from './parts/FiltersBar';
import GridTable from './parts/GridTable';
import P_A_V_info from './parts/P_A_V_info';
import StickySaveBar from './parts/StickySaveBar';

// Import utilities and hooks
import { useDateManagement } from './helpers/make_month_days';
import { useAbsenceData } from './save_and_changes/grid_memory';
import { useGridActions } from './save_and_changes/save_actions';

// Import styles
import '../../css_design/components/Views/AbsenceGrid.css';

function AbsencesPage() {
  const { employees, absenceTypes, pendingCommand } = useDataMemoryState();
  const { clearCommand } = useDataMemoryDispatch();
  const { query } = useSearchMemoryState();
  const { showNotification } = useAppMemory();
  const { showQueryPopup } = useChatbotMemoryDispatch();

  // Date management hook
  const {
    selectedYear,
    selectedMonthIndex,
    isDatePickerOpen,
    daysInSelectedMonth,
    days,
    getFormattedDate,
    isCurrentMonth,
    datePickerProps,
    handleCloseDatePicker
  } = useDateManagement();

  // Absence data management hook
  const {
    absenceData,
    isLoading,
    hasChanges,
    recentChanges,
    loadAbsenceData,
    handleSaveChanges,
    setAbsenceData,
    setHasChanges,
    setRecentChanges,
    revertAllChanges
  } = useAbsenceData(selectedYear, selectedMonthIndex, daysInSelectedMonth, showNotification);

  // Grid actions hook - optimized to prevent re-renders
  const {
    editingCell,
    selectedDepartment,
    showEmailModal,
    isExporting,
    isLoadingEmail,
    handleCellClick,
    handleCancelEdit,
    handleStatusChange,
    handleDepartmentChange,
    handleClearFilters,
    handleExportToExcel,
    handleSendEmail,
    handleOpenEmailModal,
    handleCloseEmailModal
  } = useGridActions(
    employees,
    absenceData,
    absenceTypes,
    days,
    getFormattedDate,
    recentChanges,
    showNotification,
    setAbsenceData,
    setHasChanges,
    setRecentChanges
  );

  // Memoized filtered employees
  const filteredEmployees = useMemo(() => {
    return employees.filter(employee => {
      const matchesSearch = !query ||
        employee.name.toLowerCase().includes(query.toLowerCase()) ||
        employee.email.toLowerCase().includes(query.toLowerCase());
      const matchesDepartment = selectedDepartment === 'All Departments' ||
        employee.department === selectedDepartment;
      return matchesSearch && matchesDepartment;
    });
  }, [employees, query, selectedDepartment]);

  // Effects
  useEffect(() => {
    if (employees.length > 0) {
      loadAbsenceData();
    }
  }, [employees, loadAbsenceData]);

  // Listen for AI commands from the Action Bus
  useEffect(() => {
    if (pendingCommand && pendingCommand.action === 'markAbsence') {
      const { employeeId, dates, status } = pendingCommand.args;
      
      // Execute the command using existing handleStatusChange for each date
      dates.forEach(date => {
        const cellKey = `${employeeId}-${date}`;
        handleStatusChange(cellKey, status, employeeId, date);
      });
      
      // Auto-save changes after AI action
      setTimeout(() => {
        handleSaveChanges();
      }, 100);
      
      // Clear the command from the bus
      clearCommand();
      
      // Show success notification
      const employee = employees.find(emp => emp.id === employeeId);
      const statusText = status === 'P' ? 'Present' : status === 'A' ? 'Absent' : 'Vacation';
      showNotification(`✅ Marked ${employee?.name} as ${statusText} for ${dates.length} date(s)`, 'success');
    }
    
    if (pendingCommand && pendingCommand.action === 'queryAbsence') {
      const { dates, statusFilter, queryType, monthYear, employeeName } = pendingCommand.args;
      
      // Query absence data for the specified dates
      const queryResults = [];
      
      // Filter employees if specific employee is requested
      const targetEmployees = employeeName 
        ? employees.filter(emp => emp.name.toLowerCase().includes(employeeName.toLowerCase()))
        : employees;
      
      dates.forEach(date => {
        targetEmployees.forEach(employee => {
          const cellKey = `${employee.id}-${date}`;
          const currentStatus = absenceData[cellKey] || 'P'; // Default to Present if no record
          
          // Check status filter
          const shouldInclude = statusFilter.includes('ALL') || statusFilter.includes(currentStatus);
          
          if (shouldInclude) {
            queryResults.push({
              employeeName: employee.name,
              employeeId: employee.id,
              date: date,
              status: currentStatus,
              department: employee.department || 'Unknown'
            });
          }
        });
      });
      
      // Determine the display date/period for the popup
      let displayDate = dates[0];
      let displayPeriod = null;
      
      if (queryType === 'byMonth' || dates.length > 7) {
        // For month queries, show the month name
        const firstDate = new Date(dates[0]);
        displayPeriod = firstDate.toLocaleDateString('en-US', { 
          month: 'long', 
          year: 'numeric' 
        });
      } else if (dates.length > 1) {
        // For date ranges, show range
        displayPeriod = `${dates[0]} to ${dates[dates.length - 1]}`;
      }
      
      // Show the query popup with results
      showQueryPopup(queryResults, displayDate, queryType, displayPeriod, employees.length);
      
      // Clear the command from the bus
      clearCommand();
      
      // Show notification about the query
      const resultCount = queryResults.length;
      let periodText;
      if (displayPeriod) {
        periodText = displayPeriod;
      } else if (dates.length === 1) {
        periodText = dates[0];
      } else {
        periodText = `${dates.length} dates`;
      }
      
      showNotification(`📊 Found ${resultCount} absence record(s) for ${periodText}`, 'info');
    }
  }, [pendingCommand, handleStatusChange, clearCommand, employees, showNotification, absenceData, showQueryPopup]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDatePickerOpen && !event.target.closest('.date-picker-main')) {
        handleCloseDatePicker();
      }
    };

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape' && isDatePickerOpen) {
        handleCloseDatePicker();
      }
    };

    if (isDatePickerOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscapeKey);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isDatePickerOpen, handleCloseDatePicker]);

  return (
    <div className="absence-grid-view">
      {/* Header */}
      <div className="view__header">
        <div className="view__title">
          <h1>📅 Absence Management Grid</h1>
          <p>Attendance management - Click cells to edit, then Save Changes</p>
          {isCurrentMonth && (
            <div className="current-month-indicator">
              <span className="material-icons">today</span>
              Current Month
            </div>
          )}
        </div>
        <div className="view__actions">
          {hasChanges && (
            <div className="changes-note">
              <span className="material-icons">warning</span>
              Unsaved changes
            </div>
          )}
          <button
            className="glass-btn glass-btn--primary"
            onClick={handleOpenEmailModal}
            title="Send Email Report"
          >
            Send Email
            <div className="btn-glow"></div>
          </button>
          <button
            className={`glass-btn glass-btn--secondary ${isExporting ? 'btn--loading' : ''}`}
            onClick={handleExportToExcel}
            disabled={isExporting}
            title="Export to Excel"
          >
            {isExporting ? 'Exporting...' : 'Export Excel'}
            <div className="btn-glow"></div>
          </button>
          <button
            className={`glass-btn ${hasChanges ? 'glass-btn--success' : 'glass-btn--disabled'}`}
            onClick={handleSaveChanges}
            disabled={!hasChanges || isLoading}
            title="Save all changes to database"
          >
            {isLoading ? 'Saving...' : hasChanges ? 'Save Changes' : 'No Changes'}
            <div className="btn-glow"></div>
          </button>
        </div>
      </div>

      {/* Filters */}
      <FiltersBar
        selectedDepartment={selectedDepartment}
        onDepartmentChange={handleDepartmentChange}
        onClearFilters={handleClearFilters}
        datePickerProps={datePickerProps}
      />

      {/* Grid */}
      <GridTable
        employees={filteredEmployees}
        days={days}
        selectedYear={selectedYear}
        selectedMonthIndex={selectedMonthIndex}
        absenceData={absenceData}
        absenceTypes={absenceTypes}
        editingCell={editingCell}
        onCellClick={handleCellClick}
        onStatusChange={handleStatusChange}
        onCancelEdit={handleCancelEdit}
      />

      {/* Legend */}
      <P_A_V_info absenceTypes={absenceTypes} />

      {/* Sticky Save Bar */}
      <StickySaveBar
        hasChanges={hasChanges}
        recentChanges={recentChanges}
        isLoading={isLoading}
        isExporting={isExporting}
        isLoadingEmail={isLoadingEmail}
        showEmailModal={showEmailModal}
        employees={employees}
        selectedMonth={getFormattedDate()}
        onSaveChanges={handleSaveChanges}
        onRevertChanges={revertAllChanges}
        onExportToExcel={handleExportToExcel}
        onSendEmail={handleSendEmail}
        onOpenEmailModal={handleOpenEmailModal}
        onCloseEmailModal={handleCloseEmailModal}
      />
    </div>
  );
}

export default React.memo(AbsencesPage);