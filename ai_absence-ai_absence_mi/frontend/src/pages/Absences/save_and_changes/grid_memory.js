// Remembers your unsaved edits (tiny & clear)
import { useState, useCallback, useMemo } from 'react';
import api from '../../../services/api';
import dataSyncService, { DATA_EVENTS } from '../../../services/dataSync';

export function useAbsenceData(selectedYear, selectedMonthIndex, daysInSelectedMonth, showNotification) {
  const [absenceData, setAbsenceData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [recentChanges, setRecentChanges] = useState([]);

  // Load absence data for the selected month
  const loadAbsenceData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Load employees with absence records from backend
      const employees = await api.employees.getAll();
      
      // Convert absence records to grid format
      const newAbsenceData = {};
      employees.forEach(employee => {
        if (employee.absenceRecords) {
          employee.absenceRecords.forEach(record => {
            const cellKey = `${employee.id}-${record.absenceDate}`;
            newAbsenceData[cellKey] = record.absenceType;
          });
        }
      });
      
      setAbsenceData(newAbsenceData);
      setHasChanges(false);
      setRecentChanges([]);
    } catch (error) {
      console.error('Failed to load absence data:', error);
      showNotification('Failed to load absence data', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [selectedYear, selectedMonthIndex, daysInSelectedMonth, showNotification]);

  // Save changes to backend
  const handleSaveChanges = useCallback(async () => {
    if (!hasChanges) return;
    
    setIsLoading(true);
    try {
      // Convert recent changes to the format expected by backend
      const changes = recentChanges.map(change => ({
        employeeId: change.employeeId,
        absenceDate: change.date,
        absenceType: change.newStatus,
        reason: 'Updated via grid'
      }));
      
      console.log('Saving changes to backend:', changes);
      
      // Send bulk update to backend
      await api.absences.bulkUpdate(changes);
      
      // Clear changes after successful save
      setHasChanges(false);
      setRecentChanges([]);
      
      // Emit event for real-time sync with other components (like calendar)
      dataSyncService.emit(DATA_EVENTS.ABSENCE_DATA_SAVED, {
        changes: changes,
        timestamp: new Date().toISOString()
      });
      
      showNotification(`Saved ${recentChanges.length} changes successfully`, 'success');
    } catch (error) {
      console.error('Failed to save changes:', error);
      showNotification('Failed to save changes', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [hasChanges, recentChanges, showNotification]);

  // Memoized helper functions
  const helpers = useMemo(() => ({
    // Add a change to recent changes
    addRecentChange: (employeeId, employeeName, date, oldStatus, newStatus) => {
      const change = {
        employeeId,
        employeeName,
        date,
        oldStatus,
        newStatus,
        timestamp: new Date().toISOString()
      };
      
      setRecentChanges(prev => {
        // Remove any existing change for the same employee/date
        const filtered = prev.filter(c => 
          !(c.employeeId === employeeId && c.date === date)
        );
        return [change, ...filtered];
      });
    },

    // Remove a change from recent changes
    removeRecentChange: (employeeId, date) => {
      setRecentChanges(prev => 
        prev.filter(c => !(c.employeeId === employeeId && c.date === date))
      );
    },

    // Get change count
    getChangeCount: () => recentChanges.length,

    // Revert all changes
    revertAllChanges: () => {
      // Restore original values from recentChanges
      setAbsenceData(prev => {
        const reverted = { ...prev };
        recentChanges.forEach(change => {
          const key = `${change.employeeId}-${change.date}`;
          if (change.oldStatus) {
            reverted[key] = change.oldStatus;
          } else {
            // If oldStatus is null/undefined, remove the entry (back to default "Present")
            delete reverted[key];
          }
        });
        return reverted;
      });
      
      // Clear all changes
      setRecentChanges([]);
      setHasChanges(false);
    }
  }), [recentChanges]);

  return {
    absenceData,
    isLoading,
    hasChanges,
    recentChanges,
    loadAbsenceData,
    handleSaveChanges,
    setAbsenceData,
    setHasChanges,
    setRecentChanges,
    ...helpers
  };
}