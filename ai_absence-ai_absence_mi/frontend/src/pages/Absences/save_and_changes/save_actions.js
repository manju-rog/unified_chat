// Save / Export / Email split out
import { useState, useCallback } from 'react';
import { makeKey } from './make_key';

export function useGridActions(
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
) {
  const [editingCell, setEditingCell] = useState(null);
  const [selectedDepartment, setSelectedDepartment] = useState('All Departments');
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isLoadingEmail, setIsLoadingEmail] = useState(false);

  // Handle cell click
  const handleCellClick = useCallback((cellKey) => {
    setEditingCell(cellKey);
  }, []);

  // Cancel cell editing
  const handleCancelEdit = useCallback(() => {
    setEditingCell(null);
  }, []);

  // Handle status change
  const handleStatusChange = useCallback((cellKey, newStatus, employeeId, isoString) => {
    const employee = employees.find(emp => emp.id === employeeId);
    if (!employee) return;

    const oldStatus = absenceData[cellKey] || 'P';
    
    // Update absence data
    setAbsenceData(prev => ({
      ...prev,
      [cellKey]: newStatus
    }));

    // Add to recent changes
    const change = {
      employeeId,
      employeeName: employee.name,
      date: isoString,
      oldStatus,
      newStatus,
      timestamp: new Date().toISOString()
    };

    setRecentChanges(prev => {
      // Remove any existing change for the same employee/date
      const filtered = prev.filter(c => 
        !(c.employeeId === employeeId && c.date === isoString)
      );
      return [change, ...filtered];
    });

    setHasChanges(true);
    setEditingCell(null);
  }, [employees, absenceData, setAbsenceData, setRecentChanges, setHasChanges]);

  // Handle department change
  const handleDepartmentChange = useCallback((department) => {
    setSelectedDepartment(department);
  }, []);

  // Clear filters
  const handleClearFilters = useCallback(() => {
    setSelectedDepartment('All Departments');
  }, []);

  // Export to Excel
  const handleExportToExcel = useCallback(async () => {
    setIsExporting(true);
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In real app, this would generate and download Excel file
      console.log('Exporting to Excel:', {
        month: getFormattedDate(),
        employees: employees.length,
        changes: recentChanges.length
      });
      
      alert('Excel export completed! (This is a demo - no actual file was created)');
    } catch (error) {
      console.error('Export failed:', error);
      showNotification('Export failed', 'error');
    } finally {
      setIsExporting(false);
    }
  }, [employees, recentChanges, getFormattedDate, showNotification]);

  // Send email
  const handleSendEmail = useCallback(async (emailData) => {
    setIsLoadingEmail(true);
    try {
      // Simulate email sending
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      console.log('Sending email:', emailData);
      
      alert(`Email sent to ${emailData.recipients.length} recipients! (This is a demo)`);
      setShowEmailModal(false);
    } catch (error) {
      console.error('Email failed:', error);
      showNotification('Failed to send email', 'error');
    } finally {
      setIsLoadingEmail(false);
    }
  }, [showNotification]);

  // Open email modal
  const handleOpenEmailModal = useCallback(() => {
    setShowEmailModal(true);
  }, []);

  // Close email modal
  const handleCloseEmailModal = useCallback(() => {
    setShowEmailModal(false);
  }, []);

  return {
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
  };
}