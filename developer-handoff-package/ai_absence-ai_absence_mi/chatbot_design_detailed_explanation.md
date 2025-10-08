# Complete Chatbot Design & Frontend Implementation

## Overview
This document provides a comprehensive explanation of the chatbot design, React implementation, Material UI usage, and complete frontend architecture for the AI-powered absence management chatbot.

## 1) Architecture Overview

### Component Hierarchy
```
Layout.jsx
└── Chatbot.jsx (Main chatbot component)
    ├── AbsenceQueryPopup.jsx (Query results modal)
    ├── Chatbot.css (Main styling)
    └── AbsenceQueryPopup.css (Modal styling)
```

### State Management Integration
```
App.jsx
├── ChatbotMemoryProvider (Chatbot state)
├── DataMemoryProvider (Application data)
├── ActionBusHandler (Command processor)
└── Layout
    └── Chatbot (UI component)
```

## 2) Material Icons Implementation

### CDN Integration
**File:** `frontend/public/index.html`
```html
<!-- Material Icons -->
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
```

### Material Icons Usage in Chatbot
**Complete Icon Inventory:**

#### Chatbot.jsx Icons:
1. **`smart_toy`** - AI assistant avatar and FAB button
2. **`close`** - Close chatbot button and FAB when open
3. **`person`** - User message avatar
4. **`error`** - System error messages
5. **`warning`** - System warning messages  
6. **`check_circle`** - System success messages
7. **`chat`** - Default message avatar
8. **`hourglass_empty`** - Loading state in send button
9. **`send`** - Send message button

#### AbsenceQueryPopup.jsx Icons:
1. **`event_available`** - Attendance report header (when people present)
2. **`event_busy`** - Absence report header (when people absent)
3. **`close`** - Close popup button
4. **`calendar_today`** - Date display and employee dates
5. **`sentiment_satisfied`** - No results found (happy face)
6. **`cancel`** - Absent status indicator
7. **`beach_access`** - Vacation status indicator
8. **`check_circle`** - Present status indicator
9. **`help`** - Unknown status indicator
10. **`check`** - "Got it!" button

### Material Icons Implementation Pattern
```javascript
// Standard Material Icon usage pattern
<span className="material-icons">icon_name</span>

// With conditional rendering
<span className="material-icons">
  {isVisible ? 'close' : 'smart_toy'}
</span>

// With styling
<span 
  className="material-icons" 
  style={{ color: statusInfo.color }}
>
  {statusInfo.icon}
</span>
```

## 3) Chatbot Component Detailed Analysis

### File: `frontend/src/components/Chatbot/Chatbot.jsx`

#### 3.1: Component Structure & Imports
```javascript
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChatbotMemoryState, useChatbotMemoryDispatch } from '../../memory/chatbot_memory';
import { useDataMemoryDispatch } from '../../memory/data_memory';
import AbsenceQueryPopup from './AbsenceQueryPopup';
import './Chatbot.css';
```

**Key Dependencies:**
- **React Hooks**: `useState`, `useRef`, `useEffect`, `useCallback`
- **Custom Hooks**: Chatbot memory and data memory integration
- **Child Components**: AbsenceQueryPopup for query results
- **Styling**: Dedicated CSS file

#### 3.2: State Management Integration
```javascript
// Chatbot-specific state from ChatbotMemory
const { 
  isVisible,        // Chatbot window visibility
  messages,         // Array of chat messages
  isLoading,        // Loading state for AI responses
  showQueryPopup,   // Query popup visibility
  queryResults,     // Query results data
  queryDate,        // Query date
  queryType,        // Type of query
  displayPeriod,    // Display period for results
  totalEmployees    // Total employee count
} = useChatbotMemoryState();

// Chatbot actions from ChatbotMemory
const { 
  toggleChatbot,    // Toggle chatbot visibility
  addUserMessage,   // Add user message to chat
  addAiMessage,     // Add AI response to chat
  addSystemMessage, // Add system message (success/error)
  setLoading,       // Set loading state
  setError,         // Set error state
  clearError,       // Clear error state
  clearMessages,    // Clear all messages
  hideQueryPopup    // Hide query popup
} = useChatbotMemoryDispatch();

// Data actions for Action Bus integration
const { executeCommand } = useDataMemoryDispatch();
```

#### 3.3: Local Component State
```javascript
const [inputValue, setInputValue] = useState('');           // Current input text
const [conversationId, setConversationId] = useState('');   // Backend conversation ID
const messagesEndRef = useRef(null);                        // Scroll to bottom reference
const inputRef = useRef(null);                              // Input focus reference
```

#### 3.4: Conversation Management
```javascript
// Generate unique conversation ID
const generateConversationId = () => {
  return 'conv_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
};

// Example generated ID: "conv_1725456789123_k2j8h9x4m"
```

**Conversation ID Flow:**
1. Generated when chatbot first loads
2. Sent with every message to backend
3. Backend uses it to maintain conversation context
4. Cleared when user clicks "Clear conversation"

#### 3.5: Backend Communication
```javascript
const callBackendAI = useCallback(async (message, convId) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      message: message,           // User's message
      conversationId: convId      // Conversation context
    })
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.response || `HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.json();
}, []);
```

**API Request Structure:**
```json
{
  "message": "mark manju absent today",
  "conversationId": "conv_1725456789123_k2j8h9x4m"
}
```

**API Response Structure:**
```json
{
  "success": true,
  "response": "✅ Got it! I've marked Manju as Absent for September 2, 2025.",
  "actionType": "markAbsence",
  "actionData": {
    "employeeId": 7,
    "employeeName": "Manju",
    "dates": ["2025-09-02"],
    "status": "A"
  },
  "conversationId": "conv_1725456789123_k2j8h9x4m"
}
```

#### 3.6: Message Processing Logic
```javascript
const handleSendMessage = useCallback(async () => {
  const message = inputValue.trim();
  if (!message || isLoading) return;

  // 1. Clear input and add user message
  setInputValue('');
  addUserMessage(message);
  clearError();

  try {
    // 2. Set loading state
    setLoading(true);
    
    // 3. Call backend AI
    const backendResponse = await callBackendAI(message, conversationId);
    
    // 4. Handle response based on actionType
    if (backendResponse.actionType === 'markAbsence') {
      // Process absence marking command
      const actionData = backendResponse.actionData;
      const aiResponse = {
        action: 'markAbsence',
        args: {
          employeeName: actionData.employeeName,
          employeeId: actionData.employeeId,
          dates: actionData.dates,
          status: actionData.status
        }
      };
      
      // Send to Action Bus
      executeCommand(aiResponse);
      
      // Add AI response to chat
      addAiMessage(backendResponse.response);
      
      // Add system confirmation
      const statusText = actionData.status === 'P' ? 'Present' : 
                        actionData.status === 'A' ? 'Absent' : 'Vacation';
      const dateText = actionData.dates.length === 1 ? actionData.dates[0] : 
                      `${actionData.dates.length} dates`;
      addSystemMessage(`Action executed: ${actionData.employeeName} → ${statusText} (${dateText})`, 'success');
      
    } else if (backendResponse.actionType === 'queryAbsence') {
      // Process query command
      const actionData = backendResponse.actionData;
      const aiResponse = {
        action: 'queryAbsence',
        args: {
          queryType: actionData.queryType,
          dates: actionData.dates,
          employeeName: actionData.employeeName || null,
          statusFilter: actionData.statusFilter || ['A', 'V']
        }
      };
      
      executeCommand(aiResponse);
      addAiMessage(backendResponse.response);
      
    } else {
      // Regular text response
      addAiMessage(backendResponse.response);
    }
    
  } catch (error) {
    // 5. Handle errors with user-friendly messages
    console.error('Chat error:', error);
    setError(error.message);
    
    let errorMessage = error.message;
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      errorMessage = "I can't connect to the backend server! 🤖 Please make sure the backend is running on http://localhost:8080";
    } else if (error.message.includes('500')) {
      errorMessage = "The backend server encountered an error! 😅 Please try again or contact your administrator.";
    } else if (error.message.includes('timeout')) {
      errorMessage = "The request timed out! ⏰ Please try again.";
    }
    
    addSystemMessage(`Error: ${errorMessage}`, 'error');
  } finally {
    // 6. Clear loading state
    setLoading(false);
  }
}, [inputValue, isLoading, conversationId, addUserMessage, addAiMessage, addSystemMessage, setLoading, setError, clearError, executeCommand, callBackendAI]);
```

#### 3.7: UI Event Handlers
```javascript
// Handle Enter key to send message
const handleKeyDown = useCallback((e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendMessage();
  }
}, [handleSendMessage]);

// Handle quick action buttons
const handleQuickAction = useCallback((action) => {
  setInputValue(action);
  inputRef.current?.focus();
}, []);

// Format message timestamps
const formatTime = useCallback((timestamp) => {
  return new Date(timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
}, []);
```

#### 3.8: Auto-scroll and Focus Management
```javascript
// Auto-scroll to bottom when new messages arrive
const scrollToBottom = useCallback(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, []);

useEffect(() => {
  scrollToBottom();
}, [messages, scrollToBottom]);

// Auto-focus input when chatbot opens
useEffect(() => {
  if (isVisible && inputRef.current) {
    setTimeout(() => inputRef.current?.focus(), 100);
  }
}, [isVisible]);
```

#### 3.9: Message Rendering System
```javascript
const renderMessage = useCallback((message) => {
  const messageClass = `message ${message.type}${message.messageType ? ` ${message.messageType}` : ''}`;
  
  // Determine avatar based on message type
  let avatar;
  switch (message.type) {
    case 'ai':
      avatar = <span className="material-icons">smart_toy</span>;
      break;
    case 'user':
      avatar = <span className="material-icons">person</span>;
      break;
    case 'system':
      avatar = message.messageType === 'error' 
        ? <span className="material-icons">error</span>
        : message.messageType === 'warning'
        ? <span className="material-icons">warning</span>
        : <span className="material-icons">check_circle</span>;
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
        {message.content}
        <div className="message-time">
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
}, [formatTime]);
```

**Message Types and Styling:**
- **`ai`** - AI responses (left-aligned, white background)
- **`user`** - User messages (right-aligned, gradient background)
- **`system`** - System messages with subtypes:
  - `success` - Green background, check_circle icon
  - `error` - Red background, error icon
  - `warning` - Yellow background, warning icon

#### 3.10: Typing Indicator
```javascript
const renderTypingIndicator = () => (
  <div className="message ai">
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
```

**Typing Animation:** Three dots with staggered bounce animation using CSS keyframes.

#### 3.11: Quick Actions System
```javascript
const quickActions = [
  "Mark Manju absent today",
  "Who was absent on August 15th?", 
  "Show me absences for August",
  "Put Ganesh on vacation next week"
];

// Rendered only when conversation is new (messages.length <= 1)
{messages.length <= 1 && (
  <div className="chatbot-quick-actions">
    {quickActions.map((action, index) => (
      <button
        key={index}
        className="quick-action-btn"
        onClick={() => handleQuickAction(action)}
      >
        {action}
      </button>
    ))}
  </div>
)}
```

## 4) Chatbot CSS Design System

### File: `frontend/src/components/Chatbot/Chatbot.css`

#### 4.1: Design Principles
- **Modern Glass Morphism**: Translucent backgrounds with blur effects
- **Gradient Accents**: Purple-blue gradients for primary elements
- **Smooth Animations**: Cubic-bezier transitions for premium feel
- **Material Design**: Following Material Design principles
- **Responsive**: Mobile-first responsive design

#### 4.2: Color Palette
```css
/* Primary Gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Message Colors */
--ai-message-bg: white;
--user-message-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--system-success-bg: #ecfdf5;
--system-error-bg: #fef2f2;
--system-warning-bg: #fffbeb;

/* Text Colors */
--primary-text: #374151;
--secondary-text: #6b7280;
--light-text: #9ca3af;
```

#### 4.3: Floating Action Button (FAB)
```css
.chatbot-fab {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.chatbot-fab:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
}
```

**FAB Features:**
- **Gradient Background**: Purple-blue gradient
- **Hover Animation**: Lifts up with enhanced shadow
- **Icon Rotation**: 180° rotation when opening/closing
- **Smooth Transitions**: Cubic-bezier easing

#### 4.4: Chat Window Design
```css
.chatbot-window {
  position: absolute;
  bottom: 80px;
  right: 0;
  width: 380px;
  height: 500px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform: translateY(20px) scale(0.95);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.chatbot-window.visible {
  transform: translateY(0) scale(1);
  opacity: 1;
}
```

**Window Features:**
- **Smooth Entry Animation**: Slides up and scales in
- **Large Border Radius**: Modern rounded corners
- **Deep Shadow**: Creates floating effect
- **Flexbox Layout**: Header, messages, input areas

#### 4.5: Message Styling System
```css
/* Base message styles */
.message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  animation: messageSlideIn 0.3s ease-out;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* User messages (right-aligned) */
.message.user {
  flex-direction: row-reverse;
}

/* Message content styling */
.message-content {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.4;
  word-wrap: break-word;
}

/* AI message styling */
.message.ai .message-content {
  background: white;
  color: #374151;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* User message styling */
.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}
```

#### 4.6: Typing Indicator Animation
```css
.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  animation: typingBounce 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typingBounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
```

#### 4.7: Input Area Design
```css
.chatbot-input-container {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chatbot-input {
  flex: 1;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  padding: 12px 16px;
  font-size: 14px;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
  max-height: 100px;
  min-height: 40px;
}

.chatbot-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.chatbot-send {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.chatbot-send:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
```

#### 4.8: Responsive Design
```css
@media (max-width: 480px) {
  .chatbot-container {
    bottom: 10px;
    right: 10px;
  }
  
  .chatbot-window {
    width: calc(100vw - 20px);
    height: calc(100vh - 100px);
    bottom: 70px;
    right: -10px;
  }
  
  .chatbot-fab {
    width: 56px;
    height: 56px;
  }
}
```

## 5) AbsenceQueryPopup Component

### File: `frontend/src/components/Chatbot/AbsenceQueryPopup.jsx`

#### 5.1: Component Purpose
The AbsenceQueryPopup displays query results when users ask questions like "Who was absent on August 15th?" It shows:
- Summary statistics
- Visual attendance bar
- Grouped employee lists by status
- Detailed date information

#### 5.2: Props Interface
```javascript
const AbsenceQueryPopup = React.memo(({ 
  isVisible,        // Boolean - popup visibility
  onClose,          // Function - close handler
  queryResults,     // Array - query result data
  queryDate,        // String - query date
  queryType,        // String - type of query
  displayPeriod,    // String - display period text
  totalEmployees    // Number - total employee count
}) => {
```

#### 5.3: Data Processing Logic
```javascript
// Group results by status, then by employee
const groupedResults = queryResults.reduce((acc, result) => {
  if (!acc[result.status]) {
    acc[result.status] = {};
  }
  
  const employeeKey = `${result.employeeName}-${result.employeeId}`;
  if (!acc[result.status][employeeKey]) {
    acc[result.status][employeeKey] = {
      employeeName: result.employeeName,
      employeeId: result.employeeId,
      department: result.department,
      dates: []
    };
  }
  
  acc[result.status][employeeKey].dates.push(result.date);
  return acc;
}, {});
```

**Data Structure Example:**
```javascript
groupedResults = {
  "A": {  // Absent
    "Manju-7": {
      employeeName: "Manju",
      employeeId: 7,
      department: "Engineering",
      dates: ["2025-09-02", "2025-09-03"]
    }
  },
  "V": {  // Vacation
    "John-5": {
      employeeName: "John",
      employeeId: 5,
      department: "Marketing", 
      dates: ["2025-09-02"]
    }
  }
}
```

#### 5.4: Status Information System
```javascript
const getStatusInfo = (status) => {
  switch (status) {
    case 'A':
      return { 
        label: 'Absent', 
        icon: 'cancel', 
        color: '#ef4444' 
      };
    case 'V':
      return { 
        label: 'Vacation', 
        icon: 'beach_access', 
        color: '#3b82f6' 
      };
    case 'P':
      return { 
        label: 'Present', 
        icon: 'check_circle', 
        color: '#10b981' 
      };
    default:
      return { 
        label: 'Unknown', 
        icon: 'help', 
        color: '#6b7280' 
      };
  }
};
```

#### 5.5: Visual Attendance Bar
```javascript
{(presentCount > 0 || absentCount > 0 || vacationCount > 0) && totalEmployees && (
  <div className="attendance-bar">
    <div className="bar-container">
      {presentCount > 0 && (
        <div 
          className="bar-segment present-bar" 
          style={{ width: `${(presentCount / totalEmployees) * 100}%` }}
          title={`${presentCount} Present`}
        />
      )}
      {absentCount > 0 && (
        <div 
          className="bar-segment absent-bar" 
          style={{ width: `${(absentCount / totalEmployees) * 100}%` }}
          title={`${absentCount} Absent`}
        />
      )}
      {vacationCount > 0 && (
        <div 
          className="bar-segment vacation-bar" 
          style={{ width: `${(vacationCount / totalEmployees) * 100}%` }}
          title={`${vacationCount} Vacation`}
        />
      )}
    </div>
  </div>
)}
```

**Bar Visualization:**
- **Green segments** - Present employees
- **Red segments** - Absent employees  
- **Blue segments** - Vacation employees
- **Gray segments** - No data available
- **Proportional widths** - Based on employee counts

## 6) AbsenceQueryPopup CSS Design

### File: `frontend/src/components/Chatbot/AbsenceQueryPopup.css`

#### 6.1: Modal Overlay System
```css
.absence-query-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: overlayFadeIn 0.3s ease-out;
}
```

**Modal Features:**
- **Full-screen overlay** with semi-transparent background
- **Backdrop blur** for modern glass effect
- **High z-index** (2000) to appear above chatbot (1000)
- **Centered content** with flexbox
- **Smooth fade-in** animation

#### 6.2: Popup Container
```css
.absence-query-popup {
  background: white;
  border-radius: 16px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: popupSlideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes popupSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```

#### 6.3: Attendance Bar Styling
```css
.bar-container {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
}

.bar-segment {
  height: 100%;
  transition: all 0.3s ease;
}

.present-bar {
  background: linear-gradient(90deg, #10b981, #059669);
}

.absent-bar {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.vacation-bar {
  background: linear-gradient(90deg, #3b82f6, #2563eb);
}

.unknown-bar {
  background: #e5e7eb;
}
```

#### 6.4: Employee List Design
```css
.employee-item {
  padding: 12px 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border-bottom: 1px solid #f1f5f9;
  transition: background-color 0.2s;
}

.employee-item:hover {
  background: #f8fafc;
}

.employee-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}
```

## 7) State Flow Integration

### 7.1: ChatbotMemory State Structure
```javascript
// Initial state in chatbot_memory.js
const initialState = {
  isVisible: false,
  messages: [
    {
      id: 1,
      type: 'ai',
      content: 'Hey there! 👋 I\'m Alex, your friendly AI assistant...',
      timestamp: new Date().toISOString()
    }
  ],
  isLoading: false,
  error: null,
  
  // Query popup state
  showQueryPopup: false,
  queryResults: null,
  queryDate: null,
  queryType: null,
  displayPeriod: null,
  totalEmployees: null
};
```

### 7.2: Message State Updates
```javascript
// Adding user message
dispatch({
  type: 'ADD_MESSAGE',
  payload: { 
    type: 'user', 
    content: 'mark manju absent today' 
  }
});

// Adding AI response
dispatch({
  type: 'ADD_MESSAGE',
  payload: { 
    type: 'ai', 
    content: '✅ Got it! I\'ve marked Manju as Absent for September 2, 2025.' 
  }
});

// Adding system message
dispatch({
  type: 'ADD_MESSAGE',
  payload: { 
    type: 'system', 
    content: 'Action executed: Manju → Absent (2025-09-02)', 
    messageType: 'success' 
  }
});
```

### 7.3: Query Popup State Updates
```javascript
// Show query popup with results
dispatch({ 
  type: 'SHOW_QUERY_POPUP', 
  payload: { 
    results: queryResults,
    date: queryDate,
    type: queryType,
    displayPeriod: displayPeriod,
    totalEmployees: totalEmployees
  } 
});

// Hide query popup
dispatch({ type: 'HIDE_QUERY_POPUP' });
```

## 8) Performance Optimizations

### 8.1: React.memo Usage
```javascript
const Chatbot = React.memo(() => {
  // Component only re-renders when props change
});

const AbsenceQueryPopup = React.memo(({ 
  isVisible, 
  onClose, 
  queryResults, 
  // ... other props
}) => {
  // Component only re-renders when these props change
});
```

### 8.2: useCallback Optimizations
```javascript
// Memoized callbacks prevent child re-renders
const handleSendMessage = useCallback(async () => {
  // Message sending logic
}, [inputValue, isLoading, conversationId, /* ... dependencies */]);

const renderMessage = useCallback((message) => {
  // Message rendering logic
}, [formatTime]);

const scrollToBottom = useCallback(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, []);
```

### 8.3: Conditional Rendering
```javascript
// Only render popup when visible
{showQueryPopup && (
  <AbsenceQueryPopup
    isVisible={showQueryPopup}
    onClose={hideQueryPopup}
    queryResults={queryResults}
    // ... other props
  />
)}

// Only render quick actions for new conversations
{messages.length <= 1 && (
  <div className="chatbot-quick-actions">
    {/* Quick action buttons */}
  </div>
)}
```

## 9) Error Handling System

### 9.1: Network Error Handling
```javascript
try {
  const backendResponse = await callBackendAI(message, conversationId);
  // Process response
} catch (error) {
  let errorMessage = error.message;
  
  if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
    errorMessage = "I can't connect to the backend server! 🤖 Please make sure the backend is running on http://localhost:8080";
  } else if (error.message.includes('500')) {
    errorMessage = "The backend server encountered an error! 😅 Please try again or contact your administrator.";
  } else if (error.message.includes('timeout')) {
    errorMessage = "The request timed out! ⏰ Please try again.";
  }
  
  addSystemMessage(`Error: ${errorMessage}`, 'error');
}
```

### 9.2: User-Friendly Error Messages
- **Network errors** → "Can't connect to server" with emoji
- **Server errors** → "Server encountered an error" with emoji  
- **Timeout errors** → "Request timed out" with emoji
- **Generic errors** → Display actual error message

### 9.3: Error Recovery
- **Retry mechanism** - Users can resend messages
- **Error state clearing** - Errors clear on next successful message
- **Graceful degradation** - Chat remains functional even with errors

## 10) Accessibility Features

### 10.1: Keyboard Navigation
```javascript
const handleKeyDown = useCallback((e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendMessage();
  }
}, [handleSendMessage]);
```

### 10.2: ARIA Labels and Roles
```javascript
<textarea
  ref={inputRef}
  className="chatbot-input"
  value={inputValue}
  onChange={(e) => setInputValue(e.target.value)}
  onKeyDown={handleKeyDown}
  placeholder="Try: 'Mark Manju absent today' or just say 'yes' if I suggest someone!"
  rows={1}
  disabled={isLoading}
  aria-label="Chat message input"
/>

<button
  className="chatbot-send"
  onClick={handleSendMessage}
  disabled={!inputValue.trim() || isLoading}
  title="Send message"
  aria-label="Send message"
>
```

### 10.3: Focus Management
```javascript
// Auto-focus input when chatbot opens
useEffect(() => {
  if (isVisible && inputRef.current) {
    setTimeout(() => inputRef.current?.focus(), 100);
  }
}, [isVisible]);
```

## 11) Mobile Responsiveness

### 11.1: Mobile Layout Adjustments
```css
@media (max-width: 480px) {
  .chatbot-window {
    width: calc(100vw - 20px);
    height: calc(100vh - 100px);
    bottom: 70px;
    right: -10px;
  }
  
  .chatbot-fab {
    width: 56px;
    height: 56px;
  }
}
```

### 11.2: Touch-Friendly Design
- **Larger touch targets** (minimum 44px)
- **Appropriate spacing** between interactive elements
- **Swipe gestures** for closing modals
- **Responsive text sizes** for readability

## 12) Future Enhancements

### 12.1: Planned Features
- **Voice input/output** - Speech recognition and synthesis
- **File attachments** - Upload documents or images
- **Rich message types** - Cards, buttons, carousels
- **Conversation history** - Persistent chat history
- **Multi-language support** - Internationalization

### 12.2: Performance Improvements
- **Message virtualization** - For long conversation histories
- **Image optimization** - Lazy loading and compression
- **Offline support** - Service worker integration
- **Real-time updates** - WebSocket integration

This completes the comprehensive explanation of the chatbot design, React implementation, Material UI usage, and complete frontend architecture. The system demonstrates modern React patterns, excellent UX design, and robust error handling.