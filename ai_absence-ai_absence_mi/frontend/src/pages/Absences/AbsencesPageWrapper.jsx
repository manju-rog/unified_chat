// Wrapper for AbsencesPage to handle save bar and changes
import React from 'react';
import AbsencesPage from './AbsencesPage';

// Simple wrapper that just renders the main page
// This allows the save bar to read changes from the grid memory
const AbsencesPageWrapper = React.memo(() => {
  return <AbsencesPage />;
});

AbsencesPageWrapper.displayName = 'AbsencesPageWrapper';

export default AbsencesPageWrapper;