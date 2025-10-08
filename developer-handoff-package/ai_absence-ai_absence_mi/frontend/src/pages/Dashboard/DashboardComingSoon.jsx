// Dashboard Coming Soon page
import React from 'react';
import ComingSoon from '../ComingSoon';

const DashboardComingSoon = React.memo(() => {
  return (
    <ComingSoon
      title="Dashboard Coming Soon"
      subtitle="We're building an amazing dashboard with real-time analytics, beautiful charts, and insightful metrics to help you manage your team effectively."
      icon="dashboard"
    />
  );
});

DashboardComingSoon.displayName = 'DashboardComingSoon';

export default DashboardComingSoon;