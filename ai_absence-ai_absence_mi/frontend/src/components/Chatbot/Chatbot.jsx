import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChatbotMemoryState, useChatbotMemoryDispatch } from '../../memory/chatbot_memory';
import { useDataMemoryDispatch } from '../../memory/data_memory';
import AbsenceQueryPopup from './AbsenceQueryPopup';
import './Chatbot.css';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import MicIcon from '@mui/icons-material/Mic';
import StopIcon from '@mui/icons-material/Stop';

const API_BASE_URL = 'http://localhost:8080/api/ai';

const Chatbot = React.memo(() => {
  const { isVisible, messages, isLoading, showQueryPopup, queryResults, queryDate, queryType, displayPeriod, totalEmployees } = useChatbotMemoryState();
  const { 
    toggleChatbot, 
    addUserMessage, 
    addAiMessage, 
    addSystemMessage, 
    setLoading, 
    setError, 
    clearError,
    clearMessages,
    hideQueryPopup
  } = useChatbotMemoryDispatch();
  
  const { executeCommand } = useDataMemoryDispatch();
  
  const [inputValue, setInputValue] = useState('');
  const [conversationId, setConversationId] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition,
  } = useSpeechRecognition();

  useEffect(() => {
    if (!conversationId) {
      setConversationId(generateConversationId());
    }
  }, [conversationId]);

  useEffect(() => {
  if (transcript) {
    setInputValue(transcript);
  }
}, [transcript]);

  const generateConversationId = () => {
    return 'conv_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
  };

  const callBackendAI = useCallback(async (message, convId) => {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        conversationId: convId
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.response || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }, []);

  const clearConversationContext = () => {
    setConversationId(generateConversationId());
  };

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (isVisible && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isVisible]);

  const handleSendMessage = useCallback(async () => {
    const message = inputValue.trim();
    if (!message || isLoading) return;

    setInputValue('');
    addUserMessage(message);
    clearError();

    try {
      setLoading(true);
      const backendResponse = await callBackendAI(message, conversationId);
      
      if (!backendResponse.success) {
        const errorMessage = backendResponse.error || backendResponse.response || 'Unknown error occurred';
        addAiMessage(errorMessage);
        addSystemMessage(`Error: ${errorMessage}`, 'error');
        return;
      }

      if (backendResponse.actionType === 'markAbsence') {
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
        executeCommand(aiResponse);
        addAiMessage(backendResponse.response);
        
        const statusText = actionData.status === 'P' ? 'Present' : actionData.status === 'A' ? 'Absent' : 'Vacation';
        const dateText = actionData.dates.length === 1 ? actionData.dates[0] : `${actionData.dates.length} dates`;
        addSystemMessage(`Action executed: ${actionData.employeeName} → ${statusText} (${dateText})`, 'success');
        
      } else if (backendResponse.actionType === 'queryAbsence') {
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
        addAiMessage(backendResponse.response);
      }
      
    } catch (error) {
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
      setLoading(false);
    }
  }, [inputValue, isLoading, conversationId, addUserMessage, addAiMessage, addSystemMessage, setLoading, setError, clearError, executeCommand, callBackendAI]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const handleQuickAction = useCallback((action) => {
    setInputValue(action);
    inputRef.current?.focus();
  }, []);

  const formatTime = useCallback((timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }, []);

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

  const renderMessage = useCallback((message) => {
    const messageClass = `message ${message.type}${message.messageType ? ` ${message.messageType}` : ''}`;
    
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

  const handleMicClick = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      SpeechRecognition.startListening();
    }
  };
   if (!browserSupportsSpeechRecognition) {
    return <div>Your browser does not support speech recognition.</div>;
  }

  const quickActions = [
    "Mark Manju absent today",
    "Who was absent on August 15th?", 
    "Show me absences for August",
    "Put Ganesh on vacation next week"
  ];

  return (
    <div className="chatbot-container">
      <button 
        className={`chatbot-fab ${isVisible ? 'open' : ''}`}
        onClick={toggleChatbot}
        title="AI Assistant"
      >
        <span className="material-icons">
          {isVisible ? 'close' : 'smart_toy'}
        </span>
      </button>

      <div className={`chatbot-window ${isVisible ? 'visible' : ''}`}>
        <div className="chatbot-header">
          <div className="chatbot-header-info">
            <div className="chatbot-avatar">
              <span className="material-icons">smart_toy</span>
            </div>
            <div>
              <h3 className="chatbot-title">AI Assistant</h3>
              <p className="chatbot-status">
                {isLoading ? 'Thinking...' : 'Online'}
              </p>
            </div>
          </div>
          <button 
            className="chatbot-close"
            onClick={toggleChatbot}
            title="Close chat"
          >
            <span className="material-icons">close</span>
          </button>
        </div>

        <div className="chatbot-messages">
          {messages.map(renderMessage)}
          {isLoading && renderTypingIndicator()}
          <div ref={messagesEndRef} />
        </div>

        <div className="chatbot-input-area">
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

          <div className="chatbot-input-container">
            <textarea
              ref={inputRef}
              className="chatbot-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Try: 'Mark Manju absent today' or just say 'yes' if I suggest someone!"
              rows={1}
              disabled={isLoading}
            />
            <button
              className="chatbot-send"
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              title="Send message"
            >
              <span className="material-icons">
                {isLoading ? 'hourglass_empty' : 'send'}
              </span>
            </button>
            <button 
              className="chatbot-send"
              onClick={handleMicClick}>
              {listening ? <StopIcon fontSize="large" /> : <MicIcon fontSize="large" />}
            </button>
          </div>

          {messages.length > 1 && (
            <div style={{ marginTop: '8px', textAlign: 'center' }}>
              <button
                onClick={() => {
                  clearMessages();
                  clearConversationContext();
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#6b7280',
                  fontSize: '12px',
                  cursor: 'pointer',
                  padding: '4px 8px'
                }}
              >
                Clear conversation
              </button>
            </div>
          )}
        </div>
      </div>

      <AbsenceQueryPopup
        isVisible={showQueryPopup}
        onClose={hideQueryPopup}
        queryResults={queryResults}
        queryDate={queryDate}
        queryType={queryType}
        displayPeriod={displayPeriod}
        totalEmployees={totalEmployees}
      />
    </div>
  );
});

Chatbot.displayName = 'Chatbot';

export default Chatbot;