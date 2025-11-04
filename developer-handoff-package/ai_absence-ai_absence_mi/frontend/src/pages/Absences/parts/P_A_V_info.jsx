// P / A / V legend component
import React from 'react';
import '../../../css_design/components/Views/AbsenceGridCells.css';

const P_A_V_info = React.memo(({ absenceTypes }) => {
  return (
    <div className="absence-legend">
      <h3>📋 Status Legend</h3>
      <div className="legend-items">
        {Object.entries(absenceTypes).map(([key, type]) => (
          <div key={key} className="legend-item">
            <div 
              className="legend-indicator"
              style={{ 
                backgroundColor: type.color,
                color: 'white'
              }}
            >
              {key}
            </div>
            <span className="legend-label">{type.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
});

P_A_V_info.displayName = 'P_A_V_info';

export default P_A_V_info;