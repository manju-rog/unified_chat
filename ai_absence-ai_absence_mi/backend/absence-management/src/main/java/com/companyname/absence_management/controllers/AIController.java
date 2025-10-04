package com.companyname.absence_management.controllers;

import com.companyname.absence_management.dto.AIAbsenceRequest;
import com.companyname.absence_management.dto.ChatRequestDTO;
import com.companyname.absence_management.dto.ChatResponseDTO;
import com.companyname.absence_management.response.ApiResponse;
import com.companyname.absence_management.services.AbsenceService;
import com.companyname.absence_management.services.AIService;
import com.companyname.absence_management.services.EmployeeService;
import com.companyname.absence_management.services.GeminiAPIService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.UUID;

@RestController
@RequestMapping("/api/ai")
@CrossOrigin(origins = "*")
public class AIController {

    private static final Logger logger = LoggerFactory.getLogger(AIController.class);
    private final AbsenceService absenceService;
    private final EmployeeService employeeService;
    private final AIService aiService;

    @Autowired
    public AIController(AbsenceService absenceService, EmployeeService employeeService, AIService aiService) {
        this.absenceService = absenceService;
        this.employeeService = employeeService;
        this.aiService = aiService;
    }

    @PostMapping("/chat")
    public Mono<ResponseEntity<ChatResponseDTO>> chat(@RequestBody ChatRequestDTO request) {
        logger.info("Chat request - Message length: {}, ConversationId: {}", 
            request.getMessage() != null ? request.getMessage().length() : 0, request.getConversationId());
        
        try {
            if (request == null) {
                return Mono.just(ResponseEntity.badRequest().body(
                    ChatResponseDTO.error("I didn't receive any request! 🤔 Please try again!", null)));
            }

            if (request.getMessage() == null || request.getMessage().trim().isEmpty()) {
                return Mono.just(ResponseEntity.badRequest().body(
                    ChatResponseDTO.error("I didn't receive any message! 🤔 Please try typing something!", 
                    request.getConversationId())));
            }

            String message = request.getMessage().trim();
            if (message.length() > 10000) {
                return Mono.just(ResponseEntity.badRequest().body(
                    ChatResponseDTO.error("That message is quite long! 📝 Could you try breaking it down into smaller parts?", 
                    request.getConversationId())));
            }

            final String conversationId = (request.getConversationId() == null || request.getConversationId().trim().isEmpty()) 
                ? UUID.randomUUID().toString() : request.getConversationId().trim();

            return aiService.processChatMessage(message, conversationId)
                    .map(response -> {
                        if (response.getConversationId() == null || response.getConversationId().trim().isEmpty()) {
                            response.setConversationId(conversationId);
                        }
                        return ResponseEntity.ok(response);
                    })
                    .doOnError(error -> logger.error("Error processing chat message: {}", error.getMessage()))
                    .onErrorResume(error -> {
                        String errorMessage;
                        HttpStatus status = HttpStatus.INTERNAL_SERVER_ERROR;
                        
                        if (error instanceof GeminiAPIService.GeminiAPIException) {
                            GeminiAPIService.GeminiAPIException geminiError = (GeminiAPIService.GeminiAPIException) error;
                            if (geminiError.getStatusCode() == 429) {
                                errorMessage = "I'm getting a bit overwhelmed with requests right now! 😅 Give me a moment and try again!";
                                status = HttpStatus.TOO_MANY_REQUESTS;
                            } else if (geminiError.getStatusCode() >= 500) {
                                errorMessage = "My AI brain is having a temporary hiccup! 🤖 Please try again in a few minutes!";
                                status = HttpStatus.BAD_GATEWAY;
                            } else {
                                errorMessage = "I'm having trouble connecting to my AI brain right now! 🤖 Please try again!";
                                status = HttpStatus.BAD_GATEWAY;
                            }
                        } else if (error instanceof java.util.concurrent.TimeoutException) {
                            errorMessage = "I'm thinking really hard but it's taking longer than usual! 🤔 Please try again!";
                            status = HttpStatus.REQUEST_TIMEOUT;
                        } else if (error instanceof IllegalArgumentException) {
                            errorMessage = "There's something wrong with your request! 🤷‍♂️ Could you try rephrasing it?";
                            status = HttpStatus.BAD_REQUEST;
                        } else {
                            errorMessage = "I ran into an unexpected problem! 😅 Please try again!";
                        }
                        
                        return Mono.just(ResponseEntity.status(status).body(
                            ChatResponseDTO.error(errorMessage, conversationId)));
                    });

        } catch (Exception e) {
            logger.error("Unexpected error in chat endpoint: {}", e.getMessage(), e);
            String conversationId = request != null ? request.getConversationId() : null;
            return Mono.just(ResponseEntity.internalServerError().body(
                ChatResponseDTO.error("I encountered an unexpected error! 😅 Please try again!", conversationId)));
        }
    }

    @PostMapping("/mark-absence")
    public ResponseEntity<ApiResponse> markAbsenceFromAI(@RequestBody AIAbsenceRequest request) {
        try {
            if (request.getEmployeeId() == null || request.getDates() == null || 
                request.getDates().isEmpty() || request.getStatus() == null) {
                return ResponseEntity.badRequest()
                    .body(new ApiResponse(false, "Missing required fields: employeeId, dates, or status", null));
            }

            if (!request.getStatus().matches("^[PAV]$")) {
                return ResponseEntity.badRequest()
                    .body(new ApiResponse(false, "Invalid status. Must be P (Present), A (Absent), or V (Vacation)", null));
            }

            if (!employeeService.existsById(request.getEmployeeId())) {
                return ResponseEntity.badRequest()
                    .body(new ApiResponse(false, "Employee not found with ID: " + request.getEmployeeId(), null));
            }

            absenceService.markAbsenceFromAI(request.getEmployeeId(), request.getDates(), 
                request.getStatus(), request.getReason());

            String message = String.format("Successfully marked employee %d as %s for %d date(s)", 
                request.getEmployeeId(), getStatusText(request.getStatus()), request.getDates().size());

            return ResponseEntity.ok(new ApiResponse(true, message, null));

        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                .body(new ApiResponse(false, "Error processing AI request: " + e.getMessage(), null));
        }
    }

    @GetMapping("/employees")
    public ResponseEntity<ApiResponse> getEmployeesForAI() {
        try {
            var employees = employeeService.getAllEmployees();
            return ResponseEntity.ok(new ApiResponse(true, "Employees retrieved successfully", employees));
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                .body(new ApiResponse(false, "Error retrieving employees: " + e.getMessage(), null));
        }
    }

    @GetMapping("/health")
    public ResponseEntity<ApiResponse> healthCheck() {
        return ResponseEntity.ok(new ApiResponse(true, "AI integration is healthy", null));
    }

    private String getStatusText(String status) {
        switch (status) {
            case "P": return "Present";
            case "A": return "Absent";
            case "V": return "Vacation";
            default: return "Unknown";
        }
    }
}