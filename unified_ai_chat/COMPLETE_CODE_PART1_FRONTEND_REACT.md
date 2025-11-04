# 📚 Complete Code - Part 1: Frontend React Component

## UnifiedChat.jsx - Main Chat Component

**File:** `frontend/src/UnifiedChat.jsx`

**Purpose:** Main React component that handles the chat interface, user interactions, and communication with the backend.

**Lines of Code:** 930 lines

---

## 📋 Table of Contents

1. [Imports & Setup](#imports--setup)
2. [State Management](#state-management)
3. [Core Functions](#core-functions)
4. [Message Rendering](#message-rendering)
5. [Event Handlers](#event-handlers)
6. [UI Components](#ui-components)

---

## 1. Imports & Setup

```javascript
import React, { useState, useEffect, useRef, useCallback } from 'react';
import './UnifiedChat.css';
import SowControls from './components/SowControls';
```

**What's imported:**
- `React hooks` - useState, useEffect, useRef, useCallback
- `CSS` - Styling for the component
- `SowControls` - Special component for SOW mode controls

---

## 2. State Management

### All State Variables:

```javascript
const [messages, setMessages] = useState([]);
// Stores all chat messages
// Type: Array of message objects
// Example: [{id: 1, role: "user", content: "Hello", timestamp: "..."}]

const [inputValue, setInputValue] = useState('');
// Current text in the input field
// Type: String

const [isLoading, setIsLoading] = useState(false);
// Loading state while waiting for API response
// Type: Boolean

const [sessionId, setSessionId] = useState(null);
// Unique session identifier
// Type: String or null

const [error, setError] = useState(null);
// Error message if something goes wrong
// Type: String or null

const [currentMode, setCurrentMode] = useState('unified');
// Current mode: 'unified', 'sow', or 'absence'
// Type: String

const [lastActiveButtonMessageId, setLastActiveButtonMessageId] = useState(null);
// Tracks which message has active buttons
// Type: Number or null
```

### Refs:

```javascript
const sessionIdRef = useRef(null);
// Persistent reference to session ID

const messagesEndRef = useRef(null);
// Reference to scroll anchor at bottom of messages

const inputRef = useRef(null);
// Reference to input field for focusing
```

### Constants:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api';
// Backend API URL from environment or default
```

---

## 3. Core Functions

### 3.1 formatMessageContent()

**Purpose:** Converts markdown-like text to HTML

```javascript
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
```

**Example:**
```
Input: "**Hello** *world*\n• Item 1"
Output: "<strong>Hello</strong> <em>world</em><br/><ul><li>Item 1</li></ul>"
```

---

### 3.2 scrollToBottom()

**Purpose:** Auto-scrolls chat to bottom when new messages arrive

```javascript
const scrollToBottom = useCallback(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, []);

useEffect(() => {
  scrollToBottom();
}, [messages, scrollToBottom]);
```

**How it works:**
1. `messagesEndRef` points to invisible div at bottom
2. `scrollIntoView()` scrolls that div into view
3. Triggered whenever `messages` array changes

---

### 3.3 handleSendMessage()

**Purpose:** Main function to send user message to backend

```javascript
const handleSendMessage = useCallback(async () => {
  const message = inputValue.trim();
  if (!message || isLoading) return;
  
  // 1. Handle theme changes for exit commands
  if (message === "exit_sow" || message.toLowerCase().includes("exit sow")) {
    setCurrentMode('unified');
  }
  
  // 2. Clear input and add user message
  setInputValue('');
  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  };
  setMessages(prev => [...prev, userMessage]);
  setError(null);
  
  // 3. Disable buttons from previous messages
  setLastActiveButtonMessageId(null);
  
  try {
    setIsLoading(true);
    
    // 4. Call backend API
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
    
    // 5. Update session ID
    if (data.session_id) {
      if (!sessionId) {
        setSessionId(data.session_id);
      }
      sessionIdRef.current = data.session_id;
    }
    
    // 6. Handle theme switching
    if (data.action_data?.theme) {
      setCurrentMode(data.action_data.theme);
    } else if (data.action_type) {
      // Auto-detect mode based on action_type
      if (data.action_type.includes('absence') && currentMode === 'unified') {
        setCurrentMode('absence');
      } else if (data.action_type.includes('sow') && !data.action_type.includes('exit')) {
        setCurrentMode('sow');
      } else if (data.action_type === 'sow_exit') {
        setCurrentMode('unified');
      }
    }
    
    // 7. Handle auto-download for SOW documents
    if (data.action_type === 'sow_document_ready' && data.action_data?.auto_download) {
      handleAutoDownload(data.action_data.download_url, data.action_data.filename);
    }
    
    // 8. Add assistant message
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
        thinking: data.thinking  // Gemini's thinking process
      }
    };
    setMessages(prev => [...prev, assistantMessage]);
    
    // 9. Set active buttons
    if (data.confirmation_buttons && data.confirmation_buttons.length > 0) {
      setLastActiveButtonMessageId(assistantMessage.id);
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
```

**Step-by-step:**
1. Validate input
2. Add user message to chat
3. Disable old buttons
4. Send POST request to backend
5. Update session ID
6. Handle theme changes
7. Handle auto-downloads
8. Add bot response
9. Enable new buttons

---

### 3.4 handleAutoDownload()

**Purpose:** Automatically downloads SOW documents

```javascript
const handleAutoDownload = useCallback((downloadUrl, filename) => {
  if (!downloadUrl) return;
  
  try {
    // Create temporary link
    const link = document.createElement('a');
    link.href = downloadUrl.startsWith('http') 
      ? downloadUrl 
      : `${API_BASE_URL.replace('/api', '')}${downloadUrl}`;
    link.download = filename || 'sow_document.docx';
    link.style.display = 'none';
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('Auto download triggered for:', filename);
  } catch (error) {
    console.error('Auto download failed:', error);
  }
}, [API_BASE_URL]);
```

---

### 3.5 sendChatMessage()

**Purpose:** Send message programmatically (used by SOW controls)

```javascript
const sendChatMessage = useCallback(async (message) => {
  // Disable old buttons
  setLastActiveButtonMessageId(null);
  
  // Handle exit commands
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
    
    // Handle silent updates (for resource +/- clicks)
    if (data.action_type === 'sow_silent_update') {
      // Update last assistant message without adding new message
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
      return; // Don't add new messages
    }
    
    // Add user and assistant messages
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    
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
        thinking: data.thinking
      }
    };
    
    setMessages(prev => [...prev, userMessage, assistantMessage]);
    
    // Set active buttons
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
```

---

## 4. Message Rendering

### 4.1 renderMessage()

**Purpose:** Renders a single message with all its components

```javascript
const renderMessage = useCallback((message) => {
  const messageClass = `message ${message.role}${message.messageType ? ` ${message.messageType}` : ''}`;
  
  // Handle download button
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
        {/* Thinking indicator */}
        {message.metadata?.thinking && message.role === 'assistant' && (
          <div className="message-thinking">
            <span className="thinking-icon">💭</span>
            <span className="thinking-text">{message.metadata.thinking}</span>
          </div>
        )}
        
        {/* Message text */}
        <div className="message-text" 
             dangerouslySetInnerHTML={{__html: formatMessageContent(message.content)}}>
        </div>
        
        {/* Disambiguation buttons */}
        {message.metadata?.disambiguationOptions && (
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
        
        {/* Confirmation buttons */}
        {message.metadata?.confirmationButtons && (
          <div className="confirmation-buttons">
            {message.metadata.confirmationButtons.map((button) => {
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
        
        {/* SOW Controls */}
        {currentMode === 'sow' && message.role === 'assistant' && message.metadata?.actionData && (
          <SowControls 
            hint={message.metadata.actionData} 
            onClick={(val) => sendChatMessage(val)} 
          />
        )}
        
        {/* Timestamp */}
        <div className="message-time">
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
}, [formatTime, handleOptionSelect, handleConfirmationClick, renderAbsenceBreakdown, 
    isLoading, lastActiveButtonMessageId, currentMode, sendChatMessage]);
```

---

### 4.2 renderAbsenceBreakdown()

**Purpose:** Renders absence data in a formatted card

```javascript
const renderAbsenceBreakdown = useCallback((data) => {
  const { start, end, employee_absences, totals } = data;
  
  // Parse month/year
  const startDate = new Date(start);
  const monthYear = startDate.toLocaleDateString('en-US', { 
    month: 'long', 
    year: 'numeric' 
  }).toUpperCase();
  
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
                      const formatted = d.toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric' 
                      });
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
```

---

**Continue to COMPLETE_CODE_PART2_FRONTEND_HANDLERS.md for event handlers and UI components...**
