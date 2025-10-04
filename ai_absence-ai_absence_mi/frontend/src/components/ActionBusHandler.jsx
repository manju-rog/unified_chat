import { useEffect } from 'react';
import { useDataMemoryState, useDataMemoryDispatch } from '../memory/data_memory';

export function ActionBusHandler() {
  const { pendingCommand } = useDataMemoryState();
  const { clearCommand, updateAbsenceData, refreshData } = useDataMemoryDispatch();

  useEffect(() => {
    if (!pendingCommand) return;

    const executeAction = async () => {
      try {
        switch (pendingCommand.action) {
          case 'markAbsence':
            await handleMarkAbsence(pendingCommand.args);
            break;
          
          case 'queryAbsence':
            await handleQueryAbsence(pendingCommand.args);
            break;
          
          default:
            console.warn('Action Bus: Unknown action:', pendingCommand.action);
        }
      } catch (error) {
        console.error('Action Bus: Error executing command:', error);
      } finally {
        clearCommand();
      }
    };

    executeAction();
  }, [pendingCommand, clearCommand, updateAbsenceData, refreshData]);

  const handleMarkAbsence = async (args) => {
    const { employeeName, employeeId, dates, status } = args;
    
    const absenceData = {};
    dates.forEach(date => {
      if (!absenceData[date]) {
        absenceData[date] = {};
      }
      absenceData[date][employeeId] = {
        status: status,
        employeeName: employeeName,
        date: date,
        timestamp: new Date().toISOString()
      };
    });

    updateAbsenceData(absenceData);
    
    setTimeout(async () => {
      try {
        await refreshData();
      } catch (error) {
        console.error('Action Bus: Failed to refresh data from backend:', error);
      }
    }, 1000);
  };

  const handleQueryAbsence = async (args) => {
    // Query results are handled by the backend and displayed in the chat
  };

  return null;
}

export default ActionBusHandler;