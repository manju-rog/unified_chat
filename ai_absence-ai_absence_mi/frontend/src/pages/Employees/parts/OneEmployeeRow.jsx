// One row with actions
import React from 'react';

const OneEmployeeRow = React.memo(({ employee, isSelected, onSelect }) => {
  // Generate avatar color based on name
  const getAvatarColor = (name) => {
    const colors = [
      '#3b82f6', '#ef4444', '#10b981', '#f59e0b', 
      '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
    ];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  // Get department badge class
  const getDepartmentBadgeClass = (department) => {
    const normalized = department.toLowerCase().replace(/\s+/g, '-');
    return `department-badge department-badge--${normalized}`;
  };

  const handleEdit = () => {
    console.log('Edit employee:', employee.id);
    // TODO: Implement edit functionality
  };

  const handleView = () => {
    console.log('View employee:', employee.id);
    // TODO: Implement view functionality
  };

  return (
    <tr className={isSelected ? 'row-selected' : ''}>
      <td className="checkbox-column">
        <input
          type="checkbox"
          className="table-checkbox"
          checked={isSelected}
          onChange={onSelect}
        />
      </td>
      
      <td className="name-column">
        <div className="employee-name-cell">
          <div 
            className="employee-avatar"
            style={{ backgroundColor: getAvatarColor(employee.name) }}
          >
            {employee.name.charAt(0).toUpperCase()}
          </div>
          <span className="employee-name">{employee.name}</span>
        </div>
      </td>
      
      <td className="email-column">
        <span className="employee-email">{employee.email}</span>
      </td>
      
      <td className="department-column">
        <span className={getDepartmentBadgeClass(employee.department)}>
          {employee.department}
        </span>
      </td>
      
      <td className="role-column">
        <span className="employee-role">{employee.role}</span>
      </td>
      
      <td className="location-column">
        <span className="employee-location">{employee.location}</span>
      </td>
      
      <td className="system-column">
        <div className="system-info">
          <div className="system-name">{employee.systemName}</div>
          <div className="system-ip">{employee.systemIP}</div>
        </div>
      </td>
      
      <td className="actions-column">
        <div className="table-actions">
          <button
            className="action-btn action-btn--edit"
            onClick={handleEdit}
            title="Edit employee"
          >
            <span className="material-icons">edit</span>
          </button>
          <button
            className="action-btn action-btn--view"
            onClick={handleView}
            title="View details"
          >
            <span className="material-icons">visibility</span>
          </button>
        </div>
      </td>
    </tr>
  );
});

OneEmployeeRow.displayName = 'OneEmployeeRow';

export default OneEmployeeRow;