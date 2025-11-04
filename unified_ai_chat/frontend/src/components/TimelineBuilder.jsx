import React, { useState, useEffect } from 'react';
import './TimelineBuilder.css';

const TimelineBuilder = ({ onComplete, initialData }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [totalSprints, setTotalSprints] = useState('');
  const [weeksPerSprint, setWeeksPerSprint] = useState('2');
  const [isValid, setIsValid] = useState(false);

  // Parse initial data if provided
  useEffect(() => {
    if (initialData) {
      // Try to extract dates and sprint info from text
      const startMatch = initialData.match(/start[:\s]+(\d{4}-\d{2}-\d{2})/i);
      const endMatch = initialData.match(/end[:\s]+(\d{4}-\d{2}-\d{2})/i);
      const sprintMatch = initialData.match(/(\d+)\s+sprints?/i);
      const weeksMatch = initialData.match(/(\d+)\s+weeks?\s+each/i);
      
      if (startMatch) setStartDate(startMatch[1]);
      if (endMatch) setEndDate(endMatch[1]);
      if (sprintMatch) setTotalSprints(sprintMatch[1]);
      if (weeksMatch) setWeeksPerSprint(weeksMatch[1]);
    }
  }, [initialData]);

  // Validate form
  useEffect(() => {
    const valid = startDate && endDate && totalSprints && weeksPerSprint &&
                  new Date(startDate) < new Date(endDate) &&
                  parseInt(totalSprints) > 0 &&
                  parseInt(weeksPerSprint) > 0;
    setIsValid(valid);
  }, [startDate, endDate, totalSprints, weeksPerSprint]);

  const handleSubmit = () => {
    if (!isValid) return;
    
    const timelineText = `TIMELINE: Start ${startDate}, End ${endDate}, ${totalSprints} sprints of ${weeksPerSprint} weeks each`;
    onComplete(timelineText);
  };

  const calculateDuration = () => {
    if (!startDate || !endDate) return null;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const diffWeeks = Math.ceil(diffDays / 7);
    const diffMonths = Math.ceil(diffDays / 30);
    return { days: diffDays, weeks: diffWeeks, months: diffMonths };
  };

  const duration = calculateDuration();

  return (
    <div className="timeline-builder">
      <div className="timeline-builder-content">
        <div className="date-inputs">
          <div className="input-group">
            <label htmlFor="start-date">Start Date</label>
            <input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="date-input"
            />
          </div>

          <div className="input-group">
            <label htmlFor="end-date">End Date</label>
            <input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              min={startDate}
              className="date-input"
            />
          </div>
        </div>

        <div className="sprint-inputs">
          <div className="input-group">
            <label htmlFor="total-sprints">Number of Sprints</label>
            <input
              id="total-sprints"
              type="number"
              min="1"
              max="100"
              value={totalSprints}
              onChange={(e) => setTotalSprints(e.target.value)}
              placeholder="12"
              className="number-input"
            />
          </div>

          <div className="input-group">
            <label htmlFor="weeks-per-sprint">Weeks per Sprint</label>
            <input
              id="weeks-per-sprint"
              type="number"
              min="1"
              max="8"
              value={weeksPerSprint}
              onChange={(e) => setWeeksPerSprint(e.target.value)}
              placeholder="2"
              className="number-input"
            />
          </div>
        </div>

        {duration && totalSprints && weeksPerSprint && (
          <div className="timeline-summary">
            <span>{startDate} to {endDate}</span>
            <span>•</span>
            <span>{duration.weeks} weeks</span>
            <span>•</span>
            <span>{totalSprints} sprints × {weeksPerSprint} weeks</span>
          </div>
        )}

        <button
          className={`timeline-submit-btn ${isValid ? 'active' : 'disabled'}`}
          onClick={handleSubmit}
          disabled={!isValid}
        >
          {isValid ? 'Use This Timeline' : 'Complete All Fields'}
        </button>
      </div>
    </div>
  );
};

export default TimelineBuilder;
