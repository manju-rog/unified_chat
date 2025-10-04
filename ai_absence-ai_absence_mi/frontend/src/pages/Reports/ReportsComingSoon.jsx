// Reports Coming Soon page
import React from 'react';
import ComingSoon from '../ComingSoon';

const ReportsComingSoon = React.memo(() => {
  return (
    <ComingSoon
      title="Reports Coming Soon"
      subtitle="Advanced reporting features are in development! Soon you'll have access to detailed analytics, custom reports, and data exports to track attendance patterns and team insights."
      icon="assessment"
    />
  );
});

ReportsComingSoon.displayName = 'ReportsComingSoon';

export default ReportsComingSoon;