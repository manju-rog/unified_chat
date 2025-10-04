import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
} from "react";

// Context for chatbot state and dispatch
const ChatbotMemoryStateContext = createContext();
const ChatbotMemoryDispatchContext = createContext();

// Initial chatbot state
const initialState = {
  isVisible: false,
  messages: [
    {
      id: 1,
      type: "ai",
      content:
        " I'm MI, your Holiday management  AI assistant,  What can I help you with?",
      timestamp: new Date().toISOString(),
    },
  ],
  isLoading: false,
  error: null,

  // Query popup state
  showQueryPopup: false,
  queryResults: null,
  queryDate: null,
  queryType: null,
  displayPeriod: null,
  totalEmployees: null,
};

// Chatbot reducer for handling chatbot-related state changes
function chatbotReducer(state, action) {
  switch (action.type) {
    case "TOGGLE_VISIBILITY":
      return {
        ...state,
        isVisible: !state.isVisible,
        error: null,
      };

    case "SET_VISIBILITY":
      return {
        ...state,
        isVisible: action.payload,
        error: null,
      };

    case "ADD_MESSAGE":
      return {
        ...state,
        messages: [
          ...state.messages,
          {
            id: Date.now(),
            ...action.payload,
            timestamp: new Date().toISOString(),
          },
        ],
      };

    case "SET_LOADING":
      return {
        ...state,
        isLoading: action.payload,
      };

    case "SET_ERROR":
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };

    case "CLEAR_ERROR":
      return {
        ...state,
        error: null,
      };

    case "CLEAR_MESSAGES":
      return {
        ...state,
        messages: [state.messages[0]], // Keep welcome message
      };

    case "SHOW_QUERY_POPUP":
      return {
        ...state,
        showQueryPopup: true,
        queryResults: action.payload.results,
        queryDate: action.payload.date,
        queryType: action.payload.type,
        displayPeriod: action.payload.displayPeriod,
        totalEmployees: action.payload.totalEmployees,
      };

    case "HIDE_QUERY_POPUP":
      return {
        ...state,
        showQueryPopup: false,
        queryResults: null,
        queryDate: null,
        queryType: null,
        displayPeriod: null,
        totalEmployees: null,
      };

    default:
      return state;
  }
}

// Chatbot memory provider component
export function ChatbotMemoryProvider({ children }) {
  const [state, dispatch] = useReducer(chatbotReducer, initialState);

  // Toggle chatbot visibility
  const toggleChatbot = useCallback(() => {
    dispatch({ type: "TOGGLE_VISIBILITY" });
  }, []);

  // Set chatbot visibility
  const setChatbotVisible = useCallback((visible) => {
    dispatch({ type: "SET_VISIBILITY", payload: visible });
  }, []);

  // Add user message
  const addUserMessage = useCallback((content) => {
    dispatch({
      type: "ADD_MESSAGE",
      payload: { type: "user", content },
    });
  }, []);

  // Add AI message
  const addAiMessage = useCallback((content) => {
    dispatch({
      type: "ADD_MESSAGE",
      payload: { type: "ai", content },
    });
  }, []);

  // Add system message (for confirmations, errors, etc.)
  const addSystemMessage = useCallback((content, messageType = "success") => {
    dispatch({
      type: "ADD_MESSAGE",
      payload: { type: "system", content, messageType },
    });
  }, []);

  // Set loading state
  const setLoading = useCallback((loading) => {
    dispatch({ type: "SET_LOADING", payload: loading });
  }, []);

  // Set error state
  const setError = useCallback((error) => {
    dispatch({ type: "SET_ERROR", payload: error });
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    dispatch({ type: "CLEAR_ERROR" });
  }, []);

  // Clear all messages except welcome
  const clearMessages = useCallback(() => {
    dispatch({ type: "CLEAR_MESSAGES" });
  }, []);

  // Show query popup
  const showQueryPopup = useCallback(
    (results, date, type, displayPeriod = null, totalEmployees = null) => {
      dispatch({
        type: "SHOW_QUERY_POPUP",
        payload: { results, date, type, displayPeriod, totalEmployees },
      });
    },
    []
  );

  // Hide query popup
  const hideQueryPopup = useCallback(() => {
    dispatch({ type: "HIDE_QUERY_POPUP" });
  }, []);

  // Memoized dispatch actions
  const dispatchActions = {
    toggleChatbot,
    setChatbotVisible,
    addUserMessage,
    addAiMessage,
    addSystemMessage,
    setLoading,
    setError,
    clearError,
    clearMessages,
    showQueryPopup,
    hideQueryPopup,
  };

  return (
    <ChatbotMemoryStateContext.Provider value={state}>
      <ChatbotMemoryDispatchContext.Provider value={dispatchActions}>
        {children}
      </ChatbotMemoryDispatchContext.Provider>
    </ChatbotMemoryStateContext.Provider>
  );
}

// Hook to access chatbot state
export function useChatbotMemoryState() {
  const context = useContext(ChatbotMemoryStateContext);
  if (!context) {
    throw new Error(
      "useChatbotMemoryState must be used within ChatbotMemoryProvider"
    );
  }
  return context;
}

// Hook to access chatbot dispatch functions
export function useChatbotMemoryDispatch() {
  const context = useContext(ChatbotMemoryDispatchContext);
  if (!context) {
    throw new Error(
      "useChatbotMemoryDispatch must be used within ChatbotMemoryProvider"
    );
  }
  return context;
}
