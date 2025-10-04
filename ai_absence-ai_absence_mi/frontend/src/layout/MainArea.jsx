// Main content area component
import React from 'react';
import { useUIMemoryState } from '../memory/ui_memory';

const MainArea = React.memo(({ children }) => {
  const { sidebarCollapsed } = useUIMemoryState();
  
  return (
    <main className={`main ${sidebarCollapsed ? 'main--expanded' : ''}`}>
      <div className="view view--active">
        {children}
      </div>
    </main>
  );
});

export default MainArea;