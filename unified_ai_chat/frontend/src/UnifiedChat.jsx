import React, { useState, useEffect, useRef, useCallback } from 'react';
import './UnifiedChat.css';

const UnifiedChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
  
  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);
  
  // Initialize chat
  useEffect(() => {
    // Add welcome message
    setMessages([{
      id: Date.now(),
      role: 'assistant',
      content: `Hi! 👋 I'm your AI assistant. I can help you with:

1. **Absence Management** - Mark employees absent/present/vacation, query absence records
2. **SOW Generation** - Create professional Statement of Work documents

What would you like to do today?`,
      timestamp: new Date().toISOString()
    }]);
  }, []);
  
  // Send message
  const handleSendMessage = useCallback(async () => {
    const message = inputValue.trim();
    if (!message || isLoading) return;
    
    // Clear input and add user message
    setInputValue('');
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setError(null);
    
    try {
      setIsLoading(true);
      
      // Call unified chat API
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();

      const resolvedDownloadUrl = data.download_url
        ? new URL(data.download_url, API_BASE_URL).toString()
        : null;
      
      // Update session ID
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }
      
      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          intent: data.intent,
          actionType: data.action_type,
          actionData: data.action_data,
          downloadUrl: resolvedDownloadUrl,
          disambiguationOptions: data.disambiguation_options,
          confirmationButtons: data.confirmation_buttons
        }
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Handle special actions
      if (resolvedDownloadUrl) {
        // Show download button
        setTimeout(() => {
          const downloadMessage = {
            id: Date.now() + 2,
            role: 'system',
            content: 'download_button',
            timestamp: new Date().toISOString(),
            metadata: {
              downloadUrl: resolvedDownloadUrl
            }
          };
          setMessages(prev => [...prev, downloadMessage]);
        }, 500);
      }
      
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message);
      
      const errorMessage = {
        id: Date.now() + 1,
        role: 'system',
        content: `Error: ${err.message}`,
        timestamp: new Date().toISOString(),
        messageType: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, sessionId, API_BASE_URL]);
  
  // Handle Enter key
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);
  
  // Quick actions
  const quickActions = [
    "Who is absent today?",
    "Show September absences",
    "Create a SOW",
    "Mark someone absent"
  ];
  
  const handleQuickAction = useCallback((action) => {
    setInputValue(action);
    inputRef.current?.focus();
  }, []);
  
  // Format timestamp
  const formatTime = useCallback((timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }, []);
  
  // Handle disambiguation option selection
  const handleOptionSelect = useCallback(async (option) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/chat/select-option`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          value: option.value,
          metadata: option.metadata
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Add user selection message
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: `Selected: ${option.label}`,
        timestamp: new Date().toISOString()
      };
      
      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          actionType: data.action_type,
          actionData: data.action_data
        }
      };
      
      setMessages(prev => [...prev, userMessage, assistantMessage]);
    } catch (err) {
      console.error('Option selection error:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, API_BASE_URL]);
  
  // Handle confirmation button click (Yes/No)
  const handleConfirmationClick = useCallback(async (buttonValue) => {
    // Just send the button value as a regular message
    setInputValue(buttonValue);
    
    // Trigger send message
    const message = buttonValue;
    if (!message || isLoading) return;
    
    setInputValue('');
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setError(null);
    
    try {
      setIsLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          actionType: data.action_type,
          actionData: data.action_data,
          confirmationButtons: data.confirmation_buttons
        }
      };
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (err) {
      console.error('Confirmation error:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, API_BASE_URL, isLoading]);
  
  // Render absence breakdown card
  const renderAbsenceBreakdown = useCallback((data) => {
    const { start, end, employee_absences, totals } = data;
    
    // Parse month/year from start date
    const startDate = new Date(start);
    const monthYear = startDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }).toUpperCase();
    
    return (
      <div className="absence-breakdown-card">
        <div className="breakdown-header">
          <h3>ABSENCE BREAKDOWN</h3>
          <div className="breakdown-period">{monthYear}</div>
        </div>
        
        <div className="breakdown-table">
          <div className="breakdown-table-header">
            <div className="col-name">NAME</div>
            <div className="col-status">STATUS</div>
            <div className="col-dates">DATES</div>
          </div>
          
          <div className="breakdown-table-body">
            {employee_absences && employee_absences.length > 0 ? (
              employee_absences.map((emp, index) => (
                <div key={index} className="breakdown-row">
                  <div className="col-name">
                    <span className="employee-name">{emp.name}</span>
                  </div>
                  <div className="col-status">
                    <span className={`status-badge ${emp.status.toLowerCase()}`}>
                      {emp.status}
                    </span>
                  </div>
                  <div className="col-dates">
                    <div className="date-pills">
                      {emp.dates.map((date, idx) => {
                        const d = new Date(date);
                        const formatted = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                        return (
                          <span key={idx} className="date-pill">
                            {formatted}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="breakdown-empty">
                <span className="material-icons">check_circle</span>
                <p>No absences recorded for this period</p>
              </div>
            )}
          </div>
        </div>
        
        {totals && (totals.absent > 0 || totals.vacation > 0) && (
          <div className="breakdown-footer">
            <div className="total-stat">
              <span className="stat-label">Total Absences:</span>
              <span className="stat-value">{totals.absent}</span>
            </div>
            <div className="total-stat">
              <span className="stat-label">Total Vacations:</span>
              <span className="stat-value">{totals.vacation}</span>
            </div>
          </div>
        )}
      </div>
    );
  }, []);
  
  // Render message
  const renderMessage = useCallback((message) => {
    const messageClass = `message ${message.role}${message.messageType ? ` ${message.messageType}` : ''}`;
    
    // Handle special message types
    if (message.content === 'download_button' && message.metadata?.downloadUrl) {
      return (
        <div key={message.id} className="message system">
          <div className="download-container">
            <button 
              className="download-button"
              onClick={() => window.open(message.metadata.downloadUrl, '_blank')}
            >
              <span className="material-icons">download</span>
              Download SOW Document
            </button>
          </div>
        </div>
      );
    }
    
    // Handle absence breakdown
    if (message.metadata?.actionData?.display_type === 'absence_breakdown') {
      return (
        <div key={message.id} className="message assistant">
          <div className="message-avatar">
            <span className="material-icons">smart_toy</span>
          </div>
          <div className="message-content">
            {renderAbsenceBreakdown(message.metadata.actionData)}
            <div className="message-time">
              {formatTime(message.timestamp)}
            </div>
          </div>
        </div>
      );
    }
    
    // Determine avatar
    let avatar;
    switch (message.role) {
      case 'assistant':
        avatar = <span className="material-icons">smart_toy</span>;
        break;
      case 'user':
        avatar = <span className="material-icons">person</span>;
        break;
      case 'system':
        avatar = message.messageType === 'error' 
          ? <span className="material-icons">error</span>
          : <span className="material-icons">info</span>;
        break;
      default:
        avatar = <span className="material-icons">chat</span>;
    }
    
    return (
      <div key={message.id} className={messageClass}>
        <div className="message-avatar">
          {avatar}
        </div>
        <div className="message-content">
          <div className="message-text">{message.content}</div>
          
          {/* Disambiguation buttons */}
          {message.metadata?.disambiguationOptions && message.metadata.disambiguationOptions.length > 0 && (
            <div className="disambiguation-options">
              {message.metadata.disambiguationOptions.map((option) => (
                <button
                  key={option.id}
                  className="disambiguation-button"
                  onClick={() => handleOptionSelect(option)}
                  disabled={isLoading}
                >
                  <span className="material-icons">person</span>
                  {option.label}
                </button>
              ))}
            </div>
          )}
          
          {/* Confirmation buttons (Yes/No) */}
          {message.metadata?.confirmationButtons && message.metadata.confirmationButtons.length > 0 && (
            <div className="confirmation-buttons">
              {message.metadata.confirmationButtons.map((button) => (
                <button
                  key={button.id}
                  className={`confirmation-button ${button.style || 'primary'}`}
                  onClick={() => handleConfirmationClick(button.value)}
                  disabled={isLoading}
                >
                  <span className="material-icons">
                    {button.value === 'yes' ? 'check_circle' : 'cancel'}
                  </span>
                  {button.label}
                </button>
              ))}
            </div>
          )}
          
          <div className="message-time">
            {formatTime(message.timestamp)}
          </div>
          {message.metadata?.intent && (
            <div className="message-intent">
              Intent: {message.metadata.intent}
            </div>
          )}
        </div>
      </div>
    );
  }, [formatTime, handleOptionSelect, handleConfirmationClick, renderAbsenceBreakdown, isLoading]);
  
  // Typing indicator
  const renderTypingIndicator = () => (
    <div className="message assistant">
      <div className="message-avatar">
        <span className="material-icons">smart_toy</span>
      </div>
      <div className="typing-indicator">
        <span>AI is thinking</span>
        <div className="typing-dots">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
      </div>
    </div>
  );
  
  // Determine if container should be expanded
  const isExpanded = messages.length > 1;
  
  return (
    <div className={`unified-chat-container ${isExpanded ? 'expanded' : ''}`}>
      {/* Hero Section - Only show when no messages */}
      {messages.length <= 1 && (
        <div className="chat-hero">
          <h1 className="hero-title">Ask AI, Know More.</h1>
          <p className="hero-subtitle">Your intelligent assistant for absence management and document generation</p>
        </div>
      )}
      
      {/* Chat Card Wrapper */}
      <div className="chat-card">
        <div className="chat-header">
          <div className="header-content">
            <span className="material-icons header-icon">smart_toy</span>
            <div className="header-text">
              <h1>AI Assistant</h1>
              {sessionId && <p className="session-badge">Active Session</p>}
            </div>
          </div>
        </div>
        
        <div className="chat-messages">
          {messages.map(renderMessage)}
          {isLoading && renderTypingIndicator()}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="chat-input-area">
        <div className="input-wrapper">
          <div className="input-container">
            <button className="input-action-btn" title="Add attachment">
              <span className="material-icons">add</span>
            </button>
            <textarea
              ref={inputRef}
              className="chat-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="How can I help you today?"
              rows={1}
              disabled={isLoading}
            />
            <button
              className="send-button"
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              title="Send message"
            >
              {isLoading ? (
                <span className="material-icons spinning">hourglass_empty</span>
              ) : (
                <span className="material-icons">send</span>
              )}
            </button>
          </div>
          
          {/* Quick Actions below input */}
          <div className="quick-actions-row">
            {quickActions.map((action, index) => (
              <button
                key={index}
                className="quick-action-chip"
                onClick={() => handleQuickAction(action)}
                disabled={isLoading}
              >
                {action}
              </button>
            ))}
          </div>
        </div>
        
        {error && (
          <div className="error-message">
            <span className="material-icons">error</span>
            {error}
          </div>
        )}
        </div>
      </div>
      {/* End Chat Card */}
    </div>
  );
};

export default UnifiedChat;
