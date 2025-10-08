package com.companyname.absence_management.exception;

/**
 * Base exception for AI service related errors
 */
public class AIServiceException extends RuntimeException {
    
    private final String userFriendlyMessage;
    private final ErrorType errorType;
    
    public enum ErrorType {
        GEMINI_API_ERROR,
        CONVERSATION_CONTEXT_ERROR,
        FUNCTION_EXECUTION_ERROR,
        PARSING_ERROR,
        TIMEOUT_ERROR,
        CONFIGURATION_ERROR
    }
    
    public AIServiceException(String message, String userFriendlyMessage, ErrorType errorType) {
        super(message);
        this.userFriendlyMessage = userFriendlyMessage;
        this.errorType = errorType;
    }
    
    public AIServiceException(String message, String userFriendlyMessage, ErrorType errorType, Throwable cause) {
        super(message, cause);
        this.userFriendlyMessage = userFriendlyMessage;
        this.errorType = errorType;
    }
    
    public String getUserFriendlyMessage() {
        return userFriendlyMessage;
    }
    
    public ErrorType getErrorType() {
        return errorType;
    }
}