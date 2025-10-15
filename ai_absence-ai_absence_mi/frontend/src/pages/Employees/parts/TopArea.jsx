// Add button area
import React from 'react';

const TopArea = React.memo(({ onAddEmployee, onImportCSV, onExport }) => {
  return (
    <div className="view__actions">
      <button 
        className="glass-btn glass-btn--primary"
        onClick={onAddEmployee}
        title="Add new employee"
      >
        Add Employee
        <div className="btn-glow"></div>
      </button>
      <button 
        className="glass-btn glass-btn--secondary"
        onClick={onImportCSV}
        title="Import from CSV"
      >
        Import CSV
        <div className="btn-glow"></div>
      </button>
      <button 
        className="glass-btn glass-btn--secondary"
        onClick={onExport}
        title="Export all employees"
      >
        Export
        <div className="btn-glow"></div>
      </button>
    </div>
  );
});

TopArea.displayName = 'TopArea';

export default TopArea;