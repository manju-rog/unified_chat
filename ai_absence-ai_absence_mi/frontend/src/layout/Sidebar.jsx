// Navigation sidebar component
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUIMemoryState } from '../memory/ui_memory';
import '../css_design/components/Layout/Sidebar.css';

// Navigation menu configuration
const menuItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: 'dashboard',
    path: '/dashboard'
  },
  {
    id: 'absences',
    label: 'Absence Grid',
    icon: 'calendar_today',
    path: '/absences'
  },
  {
    id: 'calendar',
    label: 'Calendar View',
    icon: 'calendar_month',
    path: '/calendar'
  },
  {
    id: 'employees',
    label: 'Employees',
    icon: 'people',
    path: '/employees'
  },
  {
    id: 'add-employee',
    label: 'Add Employee',
    icon: 'person_add',
    path: '/add-employee'
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: 'assessment',
    path: '/reports'
  }
];

// Sidebar navigation component
const Sidebar = React.memo(() => {
  const { sidebarCollapsed } = useUIMemoryState();
  const navigate = useNavigate();
  const location = useLocation();
  
  const handleNavigation = (path) => {
    navigate(path);
  };
  
  const isActive = (path) => {
    return location.pathname === path;
  };
  
  return (
    <aside className={`sidebar ${sidebarCollapsed ? 'sidebar--collapsed' : ''}`}>
      <div className="sidebar__content">
        <nav className="sidebar__nav">
          <ul className="sidebar__menu">
            {menuItems.map((item) => (
              <li
                key={item.id}
                className={`sidebar__item ${
                  isActive(item.path) ? 'sidebar__item--active' : ''
                }`}
                onClick={() => handleNavigation(item.path)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleNavigation(item.path);
                  }
                }}
              >
                <span className="material-icons">{item.icon}</span>
                <span className="sidebar__item-label">{item.label}</span>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </aside>
  );
});

export default Sidebar;