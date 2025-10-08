package com.companyname.absence_management.exception;

import com.companyname.absence_management.dto.ChatResponseDTO;
import com.companyname.absence_management.response.ApiResponse;
import com.companyname.absence_management.services.GeminiAPIService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(EmployeeIdAlreadyExistsException.class)
    public ResponseEntity<ApiResponse> handleEmployeeIdExists(EmployeeIdAlreadyExistsException ex) {
        logger.warn("Employee ID already exists: {}", ex.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(new ApiResponse(false, ex.getMessage(), null));
    }

    @ExceptionHandler(EmployeeEmailAlreadyExistsException.class)
    public ResponseEntity<ApiResponse> handleEmployeeEmailExists(EmployeeEmailAlreadyExistsException ex) {
        logger.warn("Employee email already exists: {}", ex.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(new ApiResponse(false, ex.getMessage(), null));
    }

    @ExceptionHandler(EmployeePhoneAlreadyExistsException.class)
    public ResponseEntity<ApiResponse> handleEmployeePhoneExists(EmployeePhoneAlreadyExistsException ex) {
        logger.warn("Employee phone already exists: {}", ex.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(new ApiResponse(false, ex.getMessage(), null));
    }

    @ExceptionHandler(EmployeeNotFoundException.class)
    public ResponseEntity<ApiResponse> handleEmployeeNotFound(EmployeeNotFoundException ex) {
        logger.warn("Employee not found: {}", ex.getMessage());
        return new ResponseEntity<>(new ApiResponse(false, ex.getMessage(), null), HttpStatus.NOT_FOUND);
    }

    @ExceptionHandler(InvalidAbsenceDataException.class)
    public ResponseEntity<ApiResponse> handleInvalidData(InvalidAbsenceDataException ex) {
        logger.warn("Invalid absence data: {}", ex.getMessage());
        return ResponseEntity.badRequest().body(new ApiResponse(false, ex.getMessage(), null));
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<ApiResponse> handleDataIntegrity(DataIntegrityViolationException ex) {
        logger.error("Database constraint violation", ex);
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(new ApiResponse(false, "Database constraint violation: " + ex.getRootCause().getMessage(), null));
    }

    /**
     * Handle AI Service specific exceptions
     */
    @ExceptionHandler(AIServiceException.class)
    public ResponseEntity<ChatResponseDTO> handleAIServiceException(AIServiceException ex) {
        logger.error("AI Service error: {} - Type: {}", ex.getMessage(), ex.getErrorType(), ex);
        
        HttpStatus status;
        switch (ex.getErrorType()) {
            case GEMINI_API_ERROR:
                status = HttpStatus.BAD_GATEWAY;
                break;
            case TIMEOUT_ERROR:
                status = HttpStatus.REQUEST_TIMEOUT;
                break;
            case CONFIGURATION_ERROR:
                status = HttpStatus.INTERNAL_SERVER_ERROR;
                break;
            case CONVERSATION_CONTEXT_ERROR:
            case FUNCTION_EXECUTION_ERROR:
            case PARSING_ERROR:
            default:
                status = HttpStatus.INTERNAL_SERVER_ERROR;
                break;
        }
        
        ChatResponseDTO errorResponse = ChatResponseDTO.error(ex.getUserFriendlyMessage(), null);
        return ResponseEntity.status(status).body(errorResponse);
    }

    /**
     * Handle Gemini API specific exceptions
     */
    @ExceptionHandler(GeminiAPIService.GeminiAPIException.class)
    public ResponseEntity<ChatResponseDTO> handleGeminiAPIException(GeminiAPIService.GeminiAPIException ex) {
        logger.error("Gemini API error: {} - Status: {}", ex.getMessage(), ex.getStatusCode(), ex);
        
        String userFriendlyMessage;
        HttpStatus responseStatus;
        
        if (ex.getStatusCode() == 429) {
            userFriendlyMessage = "I'm getting a bit overwhelmed with requests right now! 😅 Give me a moment to catch my breath and try again!";
            responseStatus = HttpStatus.TOO_MANY_REQUESTS;
        } else if (ex.getStatusCode() == 401 || ex.getStatusCode() == 403) {
            userFriendlyMessage = "Oops! I seem to have lost my credentials. 🔑 Please contact your administrator - there might be a configuration issue!";
            responseStatus = HttpStatus.INTERNAL_SERVER_ERROR; // Don't expose auth issues to client
        } else if (ex.getStatusCode() >= 500) {
            userFriendlyMessage = "My AI brain is having a temporary hiccup! 🤖 The service seems to be down. Please try again in a few minutes!";
            responseStatus = HttpStatus.BAD_GATEWAY;
        } else if (ex.getStatusCode() == 408) {
            userFriendlyMessage = "I'm thinking really hard about your request but it's taking longer than usual! 🤔 Please try again - I promise to be faster next time!";
            responseStatus = HttpStatus.REQUEST_TIMEOUT;
        } else {
            userFriendlyMessage = "I'm having trouble connecting to my AI brain right now. 🤖 Please try again in a moment!";
            responseStatus = HttpStatus.BAD_GATEWAY;
        }
        
        ChatResponseDTO errorResponse = ChatResponseDTO.error(userFriendlyMessage, null);
        return ResponseEntity.status(responseStatus).body(errorResponse);
    }

    /**
     * Handle conversation context specific exceptions
     */
    @ExceptionHandler(ConversationContextException.class)
    public ResponseEntity<ChatResponseDTO> handleConversationContextException(ConversationContextException ex) {
        logger.error("Conversation context error: {}", ex.getMessage(), ex);
        
        ChatResponseDTO errorResponse = ChatResponseDTO.error(ex.getUserFriendlyMessage(), null);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
    }

    /**
     * Handle illegal argument exceptions (validation errors)
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiResponse> handleIllegalArgument(IllegalArgumentException ex) {
        logger.warn("Validation error: {}", ex.getMessage());
        return ResponseEntity.badRequest()
                .body(new ApiResponse(false, "Invalid request: " + ex.getMessage(), null));
    }

    /**
     * Handle timeout exceptions
     */
    @ExceptionHandler(java.util.concurrent.TimeoutException.class)
    public ResponseEntity<ChatResponseDTO> handleTimeoutException(java.util.concurrent.TimeoutException ex) {
        logger.error("Timeout error: {}", ex.getMessage(), ex);
        
        String userFriendlyMessage = "The request is taking longer than expected! ⏰ Please try again, and if this keeps happening, try with a simpler request.";
        ChatResponseDTO errorResponse = ChatResponseDTO.error(userFriendlyMessage, null);
        return ResponseEntity.status(HttpStatus.REQUEST_TIMEOUT).body(errorResponse);
    }

    /**
     * Handle network/connection exceptions
     */
    @ExceptionHandler({java.net.ConnectException.class, java.net.UnknownHostException.class})
    public ResponseEntity<ChatResponseDTO> handleNetworkException(Exception ex) {
        logger.error("Network error: {}", ex.getMessage(), ex);
        
        String userFriendlyMessage = "I can't seem to reach my AI brain right now - there might be a network issue! 📡 Please try again in a moment!";
        ChatResponseDTO errorResponse = ChatResponseDTO.error(userFriendlyMessage, null);
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(errorResponse);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse> handleGenericException(Exception ex) {
        logger.error("Unexpected error", ex);
        
        // Don't expose internal error details to the client
        String message = "An unexpected error occurred. Please try again, and if the problem persists, contact your administrator.";
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new ApiResponse(false, message, null));
    }
}
