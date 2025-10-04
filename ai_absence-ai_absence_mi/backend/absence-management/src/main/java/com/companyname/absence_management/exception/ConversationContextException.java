package com.companyname.absence_management.exception;

/**
 * Exception for conversation context related errors
 */
public class ConversationContextException extends AIServiceException {
    
    public ConversationContextException(String message, String userFriendlyMessage) {
        super(message, userFriendlyMessage, ErrorType.CONVERSATION_CONTEXT_ERROR);
    }
    
    public ConversationContextException(String message, String userFriendlyMessage, Throwable cause) {
        super(message, userFriendlyMessage, ErrorType.CONVERSATION_CONTEXT_ERROR, cause);
    }
}