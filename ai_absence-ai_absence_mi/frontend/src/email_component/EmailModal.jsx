// Email sending modal component
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import '../css_design/components/UI/EmailModal.css';

const EmailModal = React.memo(({ 
  isOpen, 
  onClose, 
  onSendEmail, 
  employees, 
  isLoading,
  recentChanges = [],
  selectedMonth = ''
}) => {
  const [selectedRecipients, setSelectedRecipients] = useState([]);
  const [emailSubject, setEmailSubject] = useState('');
  const [emailMessage, setEmailMessage] = useState('');

  const quickOptions = useMemo(() => [
    { 
      id: 'everyone', 
      name: 'Everyone', 
      icon: '👥',
      count: employees.length
    },
    { 
      id: 'managers', 
      name: 'Managers', 
      icon: '👔',
      count: employees.filter(emp => 
        emp.role.toLowerCase().includes('manager') || 
        emp.role.toLowerCase().includes('lead')
      ).length
    },
    { 
      id: 'developers', 
      name: 'Developers', 
      icon: '💻',
      count: employees.filter(emp => emp.department === 'Development').length
    }
  ], [employees]);

  useEffect(() => {
    if (isOpen) {
      setSelectedRecipients([]);
      setEmailSubject(`Attendance Changes - ${selectedMonth}`);
      setEmailMessage(formatChangesForEmail());
    }
  }, [isOpen, recentChanges, selectedMonth]);

  const formatChangesForEmail = useCallback(() => {
    if (recentChanges.length === 0) {
      return 'No recent changes to report.';
    }

    const getStatusText = (status) => {
      switch (status) {
        case 'A': return 'Absent';
        case 'V': return 'On Vacation';
        case 'P': return 'Present';
        default: return status;
      }
    };

    const formatDate = (dateStr) => {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    };

    let message = 'Recent attendance changes:\n\n';
    recentChanges.forEach((change, index) => {
      const changeText = change.newStatus === 'P' 
        ? `${change.employeeName} will be Present on ${formatDate(change.date)}`
        : `${change.employeeName} will be ${getStatusText(change.newStatus)} on ${formatDate(change.date)}`;
      message += `${index + 1}. ${changeText}\n`;
    });
    message += `\nTotal changes: ${recentChanges.length}`;
    return message;
  }, [recentChanges]);

  const handleQuickSelect = useCallback((optionId) => {
    let recipients = [];
    switch (optionId) {
      case 'everyone':
        recipients = employees;
        break;
      case 'managers':
        recipients = employees.filter(emp => 
          emp.role.toLowerCase().includes('manager') || 
          emp.role.toLowerCase().includes('lead')
        );
        break;
      case 'developers':
        recipients = employees.filter(emp => emp.department === 'Development');
        break;
    }
    setSelectedRecipients(recipients);
  }, [employees]);

  const toggleRecipient = useCallback((employee) => {
    setSelectedRecipients(prev => {
      const exists = prev.find(emp => emp.id === employee.id);
      if (exists) {
        return prev.filter(emp => emp.id !== employee.id);
      } else {
        return [...prev, employee];
      }
    });
  }, []);

  const handleSend = useCallback(() => {
    if (selectedRecipients.length === 0) {
      alert('Please select at least one recipient');
      return;
    }
    const emailData = {
      recipients: selectedRecipients.map(emp => emp.email),
      subject: emailSubject,
      message: emailMessage,
      template: 'attendance_report'
    };
    onSendEmail(emailData);
  }, [selectedRecipients, emailSubject, emailMessage, onSendEmail]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="email-modal-simple">
        <div className="email-header-simple">
          <h2>
            {recentChanges.length > 0 ? 
             `📧 Send ${recentChanges.length} Changes` : 
             '📧 Send Report'}
          </h2>
          <button className="close-btn-simple" onClick={onClose}>×</button>
        </div>
        
        <div className="email-content-simple">
          <div className="section">
            <h3>Who should receive this?</h3>
            <div className="quick-options-simple">
              {quickOptions.map(option => (
                <button
                  key={option.id}
                  className={`quick-btn ${selectedRecipients.length === option.count ? 'selected' : ''}`}
                  onClick={() => handleQuickSelect(option.id)}
                >
                  <span className="btn-icon">{option.icon}</span>
                  <span className="btn-text">{option.name}</span>
                  <span className="btn-count">{option.count}</span>
                </button>
              ))}
            </div>
          </div>
          
          <div className="section">
            <h3>Or choose specific people:</h3>
            <div className="people-list">
              {employees.map(employee => (
                <label key={employee.id} className="person-item">
                  <input
                    type="checkbox"
                    checked={selectedRecipients.find(emp => emp.id === employee.id) ? true : false}
                    onChange={() => toggleRecipient(employee)}
                  />
                  <div className="person-info">
                    <div className="person-name">{employee.name}</div>
                    <div className="person-role">{employee.role} • {employee.department}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
          
          {recentChanges.length > 0 && (
            <div className="section">
              <h3>📋 Changes to be sent:</h3>
              <div className="changes-preview">
                {recentChanges.map((change, index) => (
                  <div key={index} className="change-item">
                    <span className="change-number">{index + 1}.</span>
                    <div className="change-details">
                      <strong>{change.employeeName}</strong> will be{' '}
                      <span className={`status-badge status-${change.newStatus.toLowerCase()}`}>
                        {change.newStatus === 'A' ? 'Absent' : 
                         change.newStatus === 'V' ? 'On Vacation' : 'Present'}
                      </span>
                      {' '}on{' '}
                      <span className="change-date">
                        {new Date(change.date).toLocaleDateString('en-US', { 
                          weekday: 'short', 
                          month: 'short', 
                          day: 'numeric' 
                        })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="section">
            <h3>Email Details</h3>
            <div className="form-simple">
              <input
                type="text"
                value={emailSubject}
                onChange={(e) => setEmailSubject(e.target.value)}
                placeholder="Email subject..."
                className="input-simple"
              />
              <textarea
                value={emailMessage}
                onChange={(e) => setEmailMessage(e.target.value)}
                placeholder="Add additional message (optional)..."
                className="textarea-simple"
                rows="4"
              />
            </div>
          </div>
        </div>
        
        <div className="email-footer-simple">
          <button className="glass-btn glass-btn--secondary" onClick={onClose}>
            Cancel
            <div className="btn-glow"></div>
          </button>
          <button 
            className={`glass-btn glass-btn--primary ${recentChanges.length > 0 ? 'has-changes' : ''}`}
            onClick={handleSend}
            disabled={selectedRecipients.length === 0 || isLoading}
          >
            {isLoading ? 'Sending...' : 
             recentChanges.length > 0 ? 
             `Send ${recentChanges.length} changes to ${selectedRecipients.length} people` :
             `Send to ${selectedRecipients.length} people`}
            <div className="btn-glow"></div>
          </button>
        </div>
      </div>
    </div>
  );
});

EmailModal.displayName = 'EmailModal';

export default EmailModal;