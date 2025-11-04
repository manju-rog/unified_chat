import React, { useState, useEffect, useRef, useCallback } from 'react';
import './UnifiedChat.css';
import SowControls from './components/SowControls';
import TimelineBuilder from './components/TimelineBuilder';

// Simple markdown formatter for message content
const formatMessageContent = (content) => {
  if (!content) return '';

  return content
    // Convert *italic* to <em>
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Convert **bold** to <strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Convert bullet points
    .replace(/^• (.+)$/gm, '<li>$1</li>')
    // Wrap consecutive <li> elements in <ul>
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    // Convert line breaks
    .replace(/\n/g, '<br/>');
};

const UnifiedChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const [currentMode, setCurrentMode] = useState('unified'); // 'unified', 'sow', 'absence'
  const [lastActiveButtonMessageId, setLastActiveButtonMessageId] = useState(null); // Track which message has active buttons
  const sessionIdRef = useRef(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api';

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // SOW generation is now handled immediately in the chat endpoint

  // Handle automatic download
  const handleAutoDownload = useCallback((downloadUrl, filename) => {
    if (!downloadUrl) return;

    try {
      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = downloadUrl.startsWith('http') ? downloadUrl : `${API_BASE_URL.replace('/api', '')}${downloadUrl}`;
      link.download = filename || 'sow_document.docx';
      link.style.display = 'none';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      console.log('Auto download triggered for:', filename);
    } catch (error) {
      console.error('Auto download failed:', error);
    }
  }, [API_BASE_URL]);

  // Only scroll when messages length changes (new message added), not on every update
  const prevMessagesLengthRef = useRef(messages.length);
  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current) {
      // New message added, scroll to bottom
      scrollToBottom();
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages.length, scrollToBottom]);

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

    // Immediately change theme if exiting SOW
    if (message === "exit_sow" || message.toLowerCase().includes("exit sow")) {
      setCurrentMode('unified');
    }

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

    // Disable buttons from previous messages when new message is sent
    setLastActiveButtonMessageId(null);

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
          mode: currentMode,
          session_id: sessionId || sessionIdRef.current
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
      if (data.session_id) {
        if (!sessionId) {
          setSessionId(data.session_id);
        }
        sessionIdRef.current = data.session_id;
      }

      // Handle mode reset
      if (data.metadata?.resetToUnified) {
        setCurrentMode('unified');
      }

      // Handle theme switching based on backend response
      if (data.action_data?.theme) {
        // Backend explicitly tells us which theme to use
        setCurrentMode(data.action_data.theme);
      } else if (data.action_type) {
        // Fallback: Auto-detect mode based on action_type
        if (data.action_type.includes('absence') && currentMode === 'unified') {
          setCurrentMode('absence');
        } else if (data.action_type.includes('sow') && !data.action_type.includes('exit') && !data.action_type.includes('generated')) {
          setCurrentMode('sow');
        } else if (data.action_type === 'sow_exit' || data.action_type === 'sow_document_generated') {
          setCurrentMode('unified');
        }
      }

      // SOW generation is now immediate - no separate loading step needed

      // Handle SOW document ready (auto download)
      if (data.action_type === 'sow_document_ready' && data.action_data?.auto_download) {
        handleAutoDownload(data.action_data.download_url, data.action_data.filename);
      }

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
          confirmationButtons: data.confirmation_buttons,
          thinking: data.thinking  // Add Gemini's thinking process
        }
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Set this message as having active buttons if it has any
      if (data.confirmation_buttons && data.confirmation_buttons.length > 0) {
        setLastActiveButtonMessageId(assistantMessage.id);
      }

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
  }, [inputValue, isLoading, sessionId, API_BASE_URL, currentMode]);

  // Send chat message function for SOW controls
  const sendChatMessage = useCallback(async (message) => {
    // Disable buttons from previous messages when new message is sent
    setLastActiveButtonMessageId(null);

    // Immediately change theme if exiting SOW
    if (message === "exit_sow" || message.toLowerCase().includes("exit sow")) {
      setCurrentMode('unified');
    }

    const payload = {
      message,
      mode: currentMode,
      session_id: sessionId || sessionIdRef.current
    };

    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (data?.metadata?.resetToUnified) {
        setCurrentMode('unified');
      }

      // Update session ID
      if (data.session_id) {
        if (!sessionId) {
          setSessionId(data.session_id);
        }
        sessionIdRef.current = data.session_id;
      }

      // Handle silent updates (for resource +/- clicks)
      if (data.action_type === 'sow_silent_update') {
        // Update the last assistant message with new action data
        setMessages(prev => {
          const newMessages = [...prev];
          const lastAssistantIndex = newMessages.map(m => m.role).lastIndexOf('assistant');
          if (lastAssistantIndex !== -1) {
            newMessages[lastAssistantIndex] = {
              ...newMessages[lastAssistantIndex],
              metadata: {
                ...newMessages[lastAssistantIndex].metadata,
                actionData: data.action_data
              }
            };
          }
          return newMessages;
        });
        return; // Don't add new messages for silent updates
      }

      // Add user message
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);

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
          downloadUrl: data.download_url,
          disambiguationOptions: data.disambiguation_options,
          confirmationButtons: data.confirmation_buttons,
          thinking: data.thinking  // Add Gemini's thinking process
        }
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Set this message as having active buttons if it has any
      if (data.confirmation_buttons && data.confirmation_buttons.length > 0) {
        setLastActiveButtonMessageId(assistantMessage.id);
      }

    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [currentMode, sessionId, API_BASE_URL]);

  // Handle Enter key
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  // Quick actions - mode-aware
  const getQuickActions = () => {
    switch (currentMode) {
      case 'sow':
        return [
          "Project overview",
          "Add deliverables",
          "Set timeline",
          "Define budget"
        ];
      case 'absence':
        return [
          "Who is absent today?",
          "Show this month's absences",
          "Mark someone absent",
          "Check vacation days"
        ];
      default:
        return [
          "Who is absent today?",
          "Show September absences",
          "Create a SOW",
          "Mark someone absent"
        ];
    }
  };

  const quickActions = getQuickActions();

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
  // Expose function globally for SowControls to populate input
  React.useEffect(() => {
    window.populateInputField = (text) => {
      setInputValue(text);
    };
    return () => {
      delete window.populateInputField;
    };
  }, []);

  const handleConfirmationClick = useCallback(async (buttonValue, populateInput) => {
    // Handle input population (new feature)
    if (populateInput) {
      setInputValue(populateInput);
      return; // Just populate input, don't send message
    }

    // Handle auto-submit buttons (backward compatibility)
    if (!buttonValue) return;

    // Check for mode changes
    if (buttonValue === "Start SOW generation" || buttonValue === "Create a SOW") {
      setCurrentMode('sow');
      sendChatMessage("/start");
      return;
    } else if (buttonValue && (buttonValue.includes("absent") || buttonValue.includes("Who is absent"))) {
      setCurrentMode('absence');
    } else if (buttonValue === "exit sow" || buttonValue === "Exit SOW Mode") {
      setCurrentMode('unified');
    }

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

  // Handle SOW mode initiation
  const handleSOWInitiation = useCallback(async () => {
    setCurrentMode('sow');
    setInputValue('Start SOW generation');

    // Send SOW start message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: 'Start SOW generation',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      setIsLoading(true);

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'Start SOW generation',
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
          actionData: data.action_data
        }
      };
      setMessages(prev => [...prev, assistantMessage]);

    } catch (err) {
      console.error('SOW initiation error:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, API_BASE_URL]);

  // Handle exit SOW mode
  const handleExitSOW = useCallback(() => {
    setCurrentMode('unified');
    const systemMessage = {
      id: Date.now(),
      role: 'system',
      content: 'Exited SOW mode. You can now ask about absence management or start a new SOW.',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, systemMessage]);
  }, []);

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

    // Handle SOW generation loading
    if (message.metadata?.actionType === 'sow_generating_loading') {
      return (
        <div key={message.id} className={messageClass}>
          <div className="message-avatar">
            {avatar}
          </div>
          <div className="message-content">
            <div className="message-text" dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }}></div>
            <div className="sow-loading-container">
              <div className="sow-loading-spinner"></div>
              <div className="sow-loading-text">Generating your professional SOW document...</div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div key={message.id} className={messageClass}>
        <div className="message-avatar">
          {avatar}
        </div>
        <div className="message-content">
          {/* Thinking indicator - show Gemini's reasoning */}
          {message.metadata?.thinking && message.role === 'assistant' && (
            <div className="message-thinking">
              <span className="thinking-icon">💭</span>
              <span className="thinking-text">{message.metadata.thinking}</span>
            </div>
          )}

          <div className="message-text" dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }}></div>

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

          {/* Confirmation buttons (Yes/No) - Hide in SOW mode, SowControls handles them */}
          {message.metadata?.confirmationButtons && message.metadata.confirmationButtons.length > 0 &&
            currentMode !== 'sow' && (
              <div className="confirmation-buttons">
                {message.metadata.confirmationButtons.map((button) => {
                  // Disable buttons if this is not the last message with active buttons
                  const isButtonActive = message.id === lastActiveButtonMessageId;
                  return (
                    <button
                      key={button.id}
                      className={`confirmation-button ${button.style || 'primary'} ${!isButtonActive ? 'disabled' : ''}`}
                      onClick={() => isButtonActive && handleConfirmationClick(button.value, button.populate_input)}
                      disabled={isLoading || !isButtonActive}
                    >
                      <span className="material-icons">
                        {(button.value === 'yes' || button.populate_input) ? 'check_circle' : 'cancel'}
                      </span>
                      {button.label}
                    </button>
                  );
                })}
              </div>
            )}

          {/* Timeline Builder - Show when timeline stage is reached */}
          {currentMode === 'sow' &&
            message.role === 'assistant' &&
            message.content &&
            (message.content.includes('Step 4: Timeline') || message.content.includes('timeline')) &&
            message.content.includes('Provide the project timeline') && (
              <TimelineBuilder
                onComplete={(timelineText) => {
                  setInputValue(timelineText);
                  inputRef.current?.focus();
                }}
                initialData={null}
              />
            )}

          {/* SOW Controls */}
          {currentMode === 'sow' && message.role === 'assistant' && message.metadata?.actionData && (
            <SowControls
              hint={message.metadata.actionData}
              onClick={(val) => sendChatMessage(val)}
            />
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
  }, [formatTime, handleOptionSelect, handleConfirmationClick, renderAbsenceBreakdown, isLoading, lastActiveButtonMessageId, currentMode, sendChatMessage]);

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
    <div className={`unified-chat-container ${isExpanded ? 'expanded' : ''} ${currentMode}`}>
      {/* Hero Section - Only show when no messages */}
      {messages.length <= 1 && (
        <div className="hero-section">
          <h1 className="hero-title">AI ABSENCE AND SOW</h1>
          <p className="hero-subtitle">Streamline absence tracking and generate professional documents with AI-powered assistance</p>
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

            {/* SOW Mode Exit Button */}
            {currentMode === 'sow' && (
              <div className="sow-mode-controls">
                <button
                  className="sow-exit-button"
                  onClick={() => sendChatMessage("exit_sow")}
                  disabled={isLoading}
                >
                  <span className="material-icons">exit_to_app</span>
                  Exit SOW Mode
                </button>
              </div>
            )}

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
