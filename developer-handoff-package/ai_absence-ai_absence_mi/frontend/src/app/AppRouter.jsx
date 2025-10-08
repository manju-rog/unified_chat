import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import useRouteSync from '../hooks/useRouteSync';
import Layout from '../layout/Layout';
import DashboardComingSoon from '../pages/Dashboard/DashboardComingSoon';
import AbsencesPageWrapper from '../pages/Absences/AbsencesPageWrapper';
import EmployeesPage from '../pages/Employees/EmployeesPage';
import ReportsComingSoon from '../pages/Reports/ReportsComingSoon';
import CalendarPage from '../pages/Calendar/CalendarPage';

// Component to handle route sync inside Router context
const AppContent = () => {
  useRouteSync(); // Sync routes with UI memory

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/absences" replace />} />
        <Route path="/dashboard" element={<DashboardComingSoon />} />
        <Route path="/absences" element={<AbsencesPageWrapper />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="/add-employee" element={<EmployeesPage />} />
        <Route path="/reports" element={<ReportsComingSoon />} />
        <Route path="*" element={<Navigate to="/absences" replace />} />
      </Routes>
    </Layout>
  );
};

const AppRouter = () => {
  return (
    <div className="App">
      <Router>
        <AppContent />
      </Router>
    </div>
  );
};

export default AppRouter;