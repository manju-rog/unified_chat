// Creative Coming Soon component for disabled features
import React, { useState, useEffect } from 'react';
import '../css_design/components/Views/ComingSoon.css';

const ComingSoon = React.memo(({ 
  title = "Coming Soon", 
  subtitle = "This feature is under development",
  icon = "construction"
}) => {
  const [dots, setDots] = useState('');

  // Animated dots effect
  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => {
        if (prev === '...') return '';
        return prev + '.';
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="coming-soon">
      {/* Clean background */}
      <div className="coming-soon__background">
        <div className="coming-soon__gradient"></div>
      </div>

      {/* Main content */}
      <div className="coming-soon__content">
        <div className="coming-soon__icon-container">
          <div className="coming-soon__icon">
            <span className="material-icons">{icon}</span>
          </div>
          <div className="coming-soon__pulse"></div>
        </div>

        <h1 className="coming-soon__title">
          {title}
          <span className="coming-soon__dots">{dots}</span>
        </h1>
        
        <p className="coming-soon__subtitle">
          {subtitle}
        </p>

        <div className="coming-soon__features">
          <div className="coming-soon__feature">
            <span className="material-icons">rocket_launch</span>
            <span>Exciting features in development</span>
          </div>
          <div className="coming-soon__feature">
            <span className="material-icons">psychology</span>
            <span>Enhanced user experience</span>
          </div>
          <div className="coming-soon__feature">
            <span className="material-icons">speed</span>
            <span>Optimized performance</span>
          </div>
        </div>

        <div className="coming-soon__progress">
          <div className="coming-soon__progress-bar">
            <div className="coming-soon__progress-fill"></div>
          </div>
          <span className="coming-soon__progress-text">Development in progress...</span>
        </div>

        <div className="coming-soon__cta">
          <p>Stay tuned for updates! 🚀</p>
        </div>
      </div>
    </div>
  );
});

ComingSoon.displayName = 'ComingSoon';

export default ComingSoon;