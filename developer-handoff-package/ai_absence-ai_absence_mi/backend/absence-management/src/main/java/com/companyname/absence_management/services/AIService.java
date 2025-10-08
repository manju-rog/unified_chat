package com.companyname.absence_management.services;

import com.companyname.absence_management.dto.*;
import com.companyname.absence_management.model.AbsenceRecord;
import com.companyname.absence_management.model.Employee;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import com.companyname.absence_management.services.GeminiAPIService.GeminiResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class AIService {
    
    private static final Logger logger = LoggerFactory.getLogger(AIService.class);
    
    private final GeminiAPIService geminiAPIService;
    private final ConversationContextService conversationContextService;
    private final AbsenceService absenceService;
    private final EmployeeService employeeService;
    private final AbsenceRecordRepository absenceRecordRepository;
    private final ObjectMapper objectMapper;
    
    @Autowired
    public AIService(GeminiAPIService geminiAPIService,
                     ConversationContextService conversationContextService,
                     AbsenceService absenceService,
                     EmployeeService employeeService,
                     AbsenceRecordRepository absenceRecordRepository,
                     ObjectMapper objectMapper) {
        this.geminiAPIService = geminiAPIService;
        this.conversationContextService = conversationContextService;
        this.absenceService = absenceService;
        this.employeeService = employeeService;
        this.absenceRecordRepository = absenceRecordRepository;
        this.objectMapper = objectMapper;
    }
    
    public Mono<ChatResponseDTO> processChatMessage(String message, String conversationId) {
        logger.info("Processing chat message for conversation: {}", conversationId);
        
        try {
            if (message == null || message.trim().isEmpty()) {
                return Mono.just(ChatResponseDTO.error("I didn't receive any message! 🤔 Please try typing something!", conversationId));
            }
            
            if (conversationId == null || conversationId.trim().isEmpty()) {
                return Mono.just(ChatResponseDTO.error("There seems to be an issue with the conversation setup. Please refresh and try again!", conversationId));
            }
            
            ConversationContext context;
            try {
                context = conversationContextService.getContext(conversationId);
            } catch (Exception e) {
                logger.error("Failed to retrieve conversation context: {}", e.getMessage());
                return Mono.just(ChatResponseDTO.error("I'm having trouble remembering our conversation! 🤯 Let's start fresh - what can I help you with?", conversationId));
            }
            
            try {
                conversationContextService.addUserMessage(conversationId, message);
            } catch (Exception e) {
                logger.error("Failed to add user message to conversation history: {}", e.getMessage());
            }
            
            if (isConfirmationResponse(message, context)) {
                return handleConfirmationResponse(message, context);
            }
            
            List<Employee> employees;
            try {
                employees = employeeService.getAllEmployees();
                if (employees.isEmpty()) {
                    return Mono.just(ChatResponseDTO.error("It looks like there are no employees in the system yet! 👥 Please add some employees first before I can help with attendance!", conversationId));
                }
            } catch (Exception e) {
                logger.error("Failed to retrieve employees: {}", e.getMessage());
                return Mono.just(ChatResponseDTO.error("I'm having trouble accessing the employee database right now! 📊 Please try again in a moment!", conversationId));
            }
            
            List<String> employeeNames = employees.stream()
                    .map(Employee::getName)
                    .collect(Collectors.toList());
            
            String systemPrompt;
            try {
                systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
            } catch (Exception e) {
                logger.error("Failed to build system prompt: {}", e.getMessage());
                return Mono.just(ChatResponseDTO.error("I'm having trouble setting up the conversation context! 🛠️ Please try again!", conversationId));
            }
            
            List<String> conversationHistory;
            try {
                conversationHistory = context.getConversationHistory().stream()
                        .map(msg -> msg.getRole() + ": " + msg.getContent())
                        .collect(Collectors.toList());
            } catch (Exception e) {
                logger.error("Failed to prepare conversation history: {}", e.getMessage());
                conversationHistory = List.of();
            }
            
            return geminiAPIService.callGeminiAPI(systemPrompt, message, conversationHistory)
                    .flatMap(response -> processGeminiResponse(response, context, employees))
                    .onErrorResume(error -> handleError(error, conversationId));
                    
        } catch (Exception e) {
            logger.error("Unexpected error processing chat message: {}", e.getMessage(), e);
            return Mono.just(ChatResponseDTO.error("I encountered an unexpected error! 😅 Please try again!", conversationId));
        }
    }
    
    private Mono<ChatResponseDTO> processGeminiResponse(GeminiResponse geminiResponse, 
                                                       ConversationContext context, 
                                                       List<Employee> employees) {
        try {
            if (geminiResponse.isTextResponse()) {
                String responseText = geminiResponse.getText();
                
                if (responseText == null || responseText.trim().isEmpty()) {
                    return Mono.just(ChatResponseDTO.error("I'm not sure what to say! 😶 Could you try rephrasing your request?", context.getConversationId()));
                }
                
                try {
                    conversationContextService.addAssistantMessage(context.getConversationId(), responseText);
                } catch (Exception e) {
                    logger.error("Failed to add assistant message to conversation history: {}", e.getMessage());
                }
                
                return Mono.just(new ChatResponseDTO(true, responseText, context.getConversationId()));
                
            } else if (geminiResponse.isFunctionCall()) {
                String functionName = geminiResponse.getFunctionName();
                JsonNode functionArgs = geminiResponse.getFunctionArgs();
                
                if (functionName == null || functionName.trim().isEmpty()) {
                    return Mono.just(ChatResponseDTO.error("I got confused about what action to take! 🤷‍♂️ Could you try rephrasing your request?", context.getConversationId()));
                }
                
                if (functionArgs == null) {
                    return Mono.just(ChatResponseDTO.error("I'm missing some important details for that action! 📝 Could you provide more information?", context.getConversationId()));
                }
                
                if ("markAbsence".equals(functionName)) {
                    return executeAbsenceAction(functionArgs, context, employees);
                } else if ("queryAbsence".equals(functionName)) {
                    return executeQueryAction(functionArgs, context, employees);
                } else {
                    return Mono.just(ChatResponseDTO.error("I'm not sure how to handle that request! 🤔 I can help you mark attendance or check who was absent. What would you like to do?", context.getConversationId()));
                }
            } else {
                return Mono.just(ChatResponseDTO.error("I received an unexpected response format! 😵 Please try again - I promise to pay better attention!", context.getConversationId()));
            }
            
        } catch (Exception e) {
            logger.error("Error processing Gemini response: {}", e.getMessage(), e);
            return Mono.just(ChatResponseDTO.error("I had trouble understanding the response! 🤯 Let me try that again - please repeat your request!", context.getConversationId()));
        }
    }
    
    private Mono<ChatResponseDTO> executeAbsenceAction(JsonNode functionArgs, 
                                                      ConversationContext context, 
                                                      List<Employee> employees) {
        try {
            if (!functionArgs.has("employeeName") || functionArgs.get("employeeName").isNull()) {
                return Mono.just(ChatResponseDTO.error("I need to know which employee you're talking about! 👤 Could you specify the employee name?", context.getConversationId()));
            }
            
            String employeeName = functionArgs.get("employeeName").asText().trim();
            if (employeeName.isEmpty()) {
                return Mono.just(ChatResponseDTO.error("The employee name seems to be empty! 👤 Could you tell me which employee you mean?", context.getConversationId()));
            }
            
            if (!functionArgs.has("status") || functionArgs.get("status").isNull()) {
                return Mono.just(ChatResponseDTO.error("I need to know what status to mark! 📝 Should they be marked as Present, Absent, or on Vacation?", context.getConversationId()));
            }
            
            String status = functionArgs.get("status").asText().trim().toUpperCase();
            if (!status.matches("^[PAV]$")) {
                return Mono.just(ChatResponseDTO.error("I don't recognize that status! 🤔 I can mark employees as Present (P), Absent (A), or on Vacation (V).", context.getConversationId()));
            }
            
            List<LocalDate> dates = new ArrayList<>();
            if (!functionArgs.has("dates") || functionArgs.get("dates").isNull()) {
                return Mono.just(ChatResponseDTO.error("I need to know which date(s) you're talking about! 📅 Could you specify the date?", context.getConversationId()));
            }
            
            JsonNode datesNode = functionArgs.get("dates");
            if (!datesNode.isArray()) {
                return Mono.just(ChatResponseDTO.error("There's something wrong with the date format! 📅 Could you try specifying the date again?", context.getConversationId()));
            }
            
            List<String> invalidDates = new ArrayList<>();
            for (JsonNode dateNode : datesNode) {
                try {
                    String dateStr = dateNode.asText();
                    LocalDate date = LocalDate.parse(dateStr);
                    dates.add(date);
                } catch (DateTimeParseException e) {
                    invalidDates.add(dateNode.asText());
                }
            }
            
            if (!invalidDates.isEmpty()) {
                return Mono.just(ChatResponseDTO.error(
                    String.format("I couldn't understand these dates: %s 📅 Please use a clear date format like 'August 15' or 'today'!", 
                    String.join(", ", invalidDates)), context.getConversationId()));
            }
            
            if (dates.isEmpty()) {
                return Mono.just(ChatResponseDTO.error("I couldn't understand any of the dates you mentioned! 📅 Please try again with a clear date like 'today' or 'August 15'!", context.getConversationId()));
            }
            
            // Find employee by name (case-insensitive)
            Optional<Employee> employeeOpt = employees.stream()
                    .filter(emp -> emp.getName().equalsIgnoreCase(employeeName))
                    .findFirst();
            
            if (employeeOpt.isEmpty()) {
                String suggestion = findClosestEmployeeName(employeeName, employees);
                if (suggestion != null) {
                    try {
                        conversationContextService.updateContext(context.getConversationId(), suggestion, "markAbsence", dates.get(0), status);
                        String responseText = String.format("I couldn't find an employee named '%s'. Did you mean '%s'? (Say yes or no) 🤔", employeeName, suggestion);
                        conversationContextService.addAssistantMessage(context.getConversationId(), responseText);
                        return Mono.just(new ChatResponseDTO(true, responseText, context.getConversationId()));
                    } catch (Exception e) {
                        logger.error("Failed to update conversation context: {}", e.getMessage());
                        return Mono.just(ChatResponseDTO.error("I found a possible match but had trouble saving it! 😅 Please try your request again!", context.getConversationId()));
                    }
                } else {
                    String availableNames = employees.stream()
                            .map(Employee::getName)
                            .limit(5)
                            .collect(Collectors.joining(", "));
                    
                    String responseText = String.format("I couldn't find an employee named '%s'! 😕 Here are some available employees: %s. Please check the spelling and try again!", 
                        employeeName, availableNames);
                    
                    try {
                        conversationContextService.addAssistantMessage(context.getConversationId(), responseText);
                    } catch (Exception e) {
                        logger.error("Failed to add assistant message: {}", e.getMessage());
                    }
                    
                    return Mono.just(new ChatResponseDTO(true, responseText, context.getConversationId()));
                }
            }
            
            Employee employee = employeeOpt.get();
            
            try {
                absenceService.markAbsenceFromAI(employee.getId(), dates, status, "Marked by AI Assistant");
            } catch (Exception e) {
                logger.error("Failed to mark absence for employee {}: {}", employee.getName(), e.getMessage());
                
                String errorMessage;
                if (e.getMessage().contains("duplicate") || e.getMessage().contains("already exists")) {
                    errorMessage = String.format("It looks like %s's attendance for some of those dates is already marked! 📝 You might want to check the attendance grid.", employee.getName());
                } else if (e.getMessage().contains("invalid") || e.getMessage().contains("constraint")) {
                    errorMessage = "There's something wrong with the attendance data! 🚫 Please check the dates and try again.";
                } else {
                    errorMessage = String.format("I had trouble saving %s's attendance! 💾 Please try again, and if this keeps happening, contact your administrator.", employee.getName());
                }
                
                return Mono.just(ChatResponseDTO.error(errorMessage, context.getConversationId()));
            }
            
            AbsenceRecord.AbsenceType absenceType = AbsenceRecord.AbsenceType.valueOf(status);
            String statusText = getStatusText(absenceType);
            String dateText = formatDatesForResponse(dates);
            String responseText = String.format("✅ Got it! I've marked %s as %s for %s.", 
                                              employee.getName(), statusText, dateText);
            
            try {
                conversationContextService.addAssistantMessage(context.getConversationId(), responseText);
            } catch (Exception e) {
                logger.error("Failed to add success message to conversation history: {}", e.getMessage());
            }
            
            Map<String, Object> actionData = new HashMap<>();
            actionData.put("employeeName", employee.getName());
            actionData.put("employeeId", employee.getId());
            actionData.put("dates", dates.stream().map(LocalDate::toString).collect(Collectors.toList()));
            actionData.put("status", status);
            
            return Mono.just(new ChatResponseDTO(true, responseText, "markAbsence", actionData, context.getConversationId()));
            
        } catch (Exception e) {
            logger.error("Unexpected error executing absence action: {}", e.getMessage(), e);
            return Mono.just(ChatResponseDTO.error("I ran into an unexpected problem while marking the absence! 😅 Please try again!", context.getConversationId()));
        }
    }
    
    /**
     * Execute absence query action
     */
    private Mono<ChatResponseDTO> executeQueryAction(JsonNode functionArgs, 
                                                    ConversationContext context, 
                                                    List<Employee> employees) {
        logger.debug("Executing query action for conversation: {} with args: {}", context.getConversationId(), functionArgs.toString());
        
        try {
            // Validate and extract query type
            if (!functionArgs.has("queryType") || functionArgs.get("queryType").isNull()) {
                logger.warn("Missing queryType in function arguments for conversation: {}", context.getConversationId());
                return Mono.just(ChatResponseDTO.error("I'm not sure what kind of query you want! 🤔 Could you be more specific about what information you need?", context.getConversationId()));
            }
            
            String queryType = functionArgs.get("queryType").asText().trim();
            if (queryType.isEmpty()) {
                logger.warn("Empty queryType in function arguments for conversation: {}", context.getConversationId());
                return Mono.just(ChatResponseDTO.error("The query type seems to be empty! 🤔 What information are you looking for?", context.getConversationId()));
            }
            
            // Parse and validate dates
            List<LocalDate> dates = new ArrayList<>();
            if (!functionArgs.has("dates") || functionArgs.get("dates").isNull()) {
                logger.warn("Missing dates in function arguments for conversation: {}", context.getConversationId());
                return Mono.just(ChatResponseDTO.error("I need to know which date(s) you're asking about! 📅 Could you specify the date?", context.getConversationId()));
            }
            
            JsonNode datesNode = functionArgs.get("dates");
            if (!datesNode.isArray()) {
                logger.warn("Dates field is not an array for conversation: {}", context.getConversationId());
                return Mono.just(ChatResponseDTO.error("There's something wrong with the date format! 📅 Could you try specifying the date again?", context.getConversationId()));
            }
            
            List<String> invalidDates = new ArrayList<>();
            for (JsonNode dateNode : datesNode) {
                try {
                    String dateStr = dateNode.asText();
                    LocalDate date = LocalDate.parse(dateStr);
                    dates.add(date);
                    logger.debug("Parsed query date: {} for conversation: {}", date, context.getConversationId());
                } catch (DateTimeParseException e) {
                    logger.warn("Invalid date format in query: {} for conversation: {}", dateNode.asText(), context.getConversationId());
                    invalidDates.add(dateNode.asText());
                }
            }
            
            if (!invalidDates.isEmpty()) {
                return Mono.just(ChatResponseDTO.error(
                    String.format("I couldn't understand these dates: %s 📅 Please use a clear date format like 'August 15' or 'today'!", 
                    String.join(", ", invalidDates)), context.getConversationId()));
            }
            
            if (dates.isEmpty()) {
                logger.warn("No valid dates found for query in conversation: {}", context.getConversationId());
                return Mono.just(ChatResponseDTO.error("I couldn't understand any of the dates you mentioned! 📅 Please try again with a clear date like 'today' or 'August 15'!", context.getConversationId()));
            }
            
            // Parse status filter with defaults
            List<String> statusFilter = new ArrayList<>();
            JsonNode statusFilterNode = functionArgs.get("statusFilter");
            if (statusFilterNode != null && statusFilterNode.isArray()) {
                for (JsonNode statusNode : statusFilterNode) {
                    String status = statusNode.asText().trim().toUpperCase();
                    if (status.matches("^(A|V|P|ALL)$")) {
                        statusFilter.add(status);
                    } else {
                        logger.warn("Invalid status filter '{}' for conversation: {}", status, context.getConversationId());
                    }
                }
            }
            
            // Default to showing absences and vacations if no filter specified
            if (statusFilter.isEmpty()) {
                statusFilter.add("A");
                statusFilter.add("V");
                logger.info("Using default status filter [A, V] for conversation: {}", context.getConversationId());
            } else {
                logger.info("Using provided status filter {} for conversation: {}", statusFilter, context.getConversationId());
            }
            
            // Get employee name if specified
            String employeeName = null;
            if (functionArgs.has("employeeName") && !functionArgs.get("employeeName").isNull()) {
                employeeName = functionArgs.get("employeeName").asText().trim();
                if (employeeName.isEmpty()) {
                    employeeName = null;
                }
            }
            
            logger.info("Processing query for conversation: {} - Type: {}, Dates: {}, StatusFilter: {}, Employee: {}", 
                context.getConversationId(), queryType, dates.size(), statusFilter, employeeName);
            
            // Execute the query with error handling
            List<AbsenceRecord> absenceRecords;
            try {
                absenceRecords = queryAbsenceRecords(dates, statusFilter, employeeName, employees);
                logger.info("Query returned {} records for conversation: {}", absenceRecords.size(), context.getConversationId());
            } catch (Exception e) {
                logger.error("Failed to execute absence query for conversation {}: {}", context.getConversationId(), e.getMessage(), e);
                
                String errorMessage;
                if (e.getMessage().contains("database") || e.getMessage().contains("connection")) {
                    errorMessage = "I'm having trouble accessing the attendance database right now! 📊 Please try again in a moment.";
                } else if (e.getMessage().contains("timeout")) {
                    errorMessage = "The query is taking longer than expected! ⏰ Please try again with a smaller date range.";
                } else {
                    errorMessage = "I ran into a problem while searching for that information! 🔍 Please try again.";
                }
                
                return Mono.just(ChatResponseDTO.error(errorMessage, context.getConversationId()));
            }
            
            // Build response with error handling
            String responseText;
            try {
                responseText = buildQueryResponse(absenceRecords, dates, statusFilter, queryType, employeeName);
                logger.debug("Built query response with {} characters for conversation: {}", responseText.length(), context.getConversationId());
            } catch (Exception e) {
                logger.error("Failed to build query response for conversation {}: {}", context.getConversationId(), e.getMessage(), e);
                return Mono.just(ChatResponseDTO.error("I found the information but had trouble formatting it! 📝 Please try your query again.", context.getConversationId()));
            }
            
            try {
                conversationContextService.addAssistantMessage(context.getConversationId(), responseText);
            } catch (Exception e) {
                logger.error("Failed to add query response to conversation history for {}: {}", context.getConversationId(), e.getMessage());
                // Continue processing even if we can't save to history
            }
            
            // Create action data for frontend
            Map<String, Object> actionData = new HashMap<>();
            actionData.put("queryType", queryType);
            actionData.put("dates", dates.stream().map(LocalDate::toString).collect(Collectors.toList()));
            actionData.put("statusFilter", statusFilter);
            actionData.put("employeeName", employeeName);
            
            try {
                actionData.put("results", absenceRecords.stream().map(this::convertAbsenceRecordToMap).collect(Collectors.toList()));
                actionData.put("totalRecords", absenceRecords.size());
            } catch (Exception e) {
                logger.error("Failed to convert absence records to maps for conversation {}: {}", context.getConversationId(), e.getMessage(), e);
                actionData.put("results", List.of()); // Empty list as fallback
                actionData.put("totalRecords", 0);
            }
            
            return Mono.just(new ChatResponseDTO(true, responseText, "queryAbsence", actionData, context.getConversationId()));
            
        } catch (Exception e) {
            logger.error("Unexpected error executing query action for conversation {}: {}", context.getConversationId(), e.getMessage(), e);
            return Mono.just(ChatResponseDTO.error("I ran into an unexpected problem while searching! 🔍 Please try your query again!", context.getConversationId()));
        }
    }
    
    /**
     * Check if the message is a confirmation response (yes/no)
     */
    private boolean isConfirmationResponse(String message, ConversationContext context) {
        if (!context.hasContext()) {
            return false;
        }
        
        String lowerMessage = message.toLowerCase().trim();
        return lowerMessage.matches("^(yes|yeah|yep|y|correct|right|ok|okay|sure|no|nope|n|wrong|incorrect)$");
    }
    
    /**
     * Handle confirmation responses (yes/no) to previous suggestions
     */
    private Mono<ChatResponseDTO> handleConfirmationResponse(String message, ConversationContext context) {
        String lowerMessage = message.toLowerCase().trim();
        boolean isPositive = lowerMessage.matches("^(yes|yeah|yep|y|correct|right|ok|okay|sure)$");
        
        if (isPositive && context.getLastSuggestedEmployee() != null) {
            // User confirmed the suggested employee name
            String employeeName = context.getLastSuggestedEmployee();
            String action = context.getLastRequestedAction();
            LocalDate date = context.getLastRequestedDate();
            String status = context.getLastRequestedStatus();
            
            // Clear the context
            conversationContextService.clearContext(context.getConversationId());
            
            if ("markAbsence".equals(action) && date != null && status != null) {
                // Find the employee and execute the action
                List<Employee> employees = employeeService.getAllEmployees();
                Optional<Employee> employeeOpt = employees.stream()
                        .filter(emp -> emp.getName().equalsIgnoreCase(employeeName))
                        .findFirst();
                
                if (employeeOpt.isPresent()) {
                    Employee employee = employeeOpt.get();
                    List<LocalDate> dates = Arrays.asList(date);
                    
                    try {
                        absenceService.markAbsenceFromAI(employee.getId(), dates, status, "Marked by AI Assistant");
                        
                        AbsenceRecord.AbsenceType absenceType = AbsenceRecord.AbsenceType.valueOf(status);
                        String statusText = getStatusText(absenceType);
                        String responseText = String.format("✅ Perfect! I've marked %s as %s for %s.", 
                                                          employee.getName(), statusText, date.format(DateTimeFormatter.ofPattern("MMMM d, yyyy")));
                        
                        conversationContextService.addAssistantMessage(context.getConversationId(), responseText);
                        
                        Map<String, Object> actionData = new HashMap<>();
                        actionData.put("employeeName", employee.getName());
                        actionData.put("employeeId", employee.getId());
                        actionData.put("dates", Arrays.asList(date.toString()));
                        actionData.put("status", status);
                        
                        return Mono.just(new ChatResponseDTO(true, responseText, "markAbsence", actionData, context.getConversationId()));
                        
                    } catch (Exception e) {
                        logger.error("Error executing confirmed absence action", e);
                        return Mono.just(ChatResponseDTO.error("I had trouble marking the absence. Please try again!", context.getConversationId()));
                    }
                }
            }
        } else if (!isPositive) {
            // User said no - clear context and ask for clarification
            conversationContextService.clearContext(context.getConversationId());
            String responseText = "No problem! Please tell me the correct employee name and I'll help you with that.";
            conversationContextService.addAssistantMessage(context.getConversationId(), responseText);
            
            return Mono.just(new ChatResponseDTO(true, responseText, context.getConversationId()));
        }
        
        // Fallback
        conversationContextService.clearContext(context.getConversationId());
        String responseText = "I'm not sure what you're referring to. Could you please repeat your request?";
        conversationContextService.addAssistantMessage(context.getConversationId(), responseText);
        
        return Mono.just(new ChatResponseDTO(true, responseText, context.getConversationId()));
    }
    
    /**
     * Query absence records based on criteria
     */
    private List<AbsenceRecord> queryAbsenceRecords(List<LocalDate> dates, List<String> statusFilter, 
                                                   String employeeName, List<Employee> employees) {
        List<AbsenceRecord> results = new ArrayList<>();
        
        logger.debug("Querying absence records for {} dates, statusFilter: {}, employee: {}", 
            dates.size(), statusFilter, employeeName);
        
        if (dates.isEmpty()) {
            logger.warn("No dates provided for query");
            return results;
        }
        
        // Optimize for date range queries
        LocalDate startDate = dates.stream().min(LocalDate::compareTo).orElse(dates.get(0));
        LocalDate endDate = dates.stream().max(LocalDate::compareTo).orElse(dates.get(0));
        
        logger.info("Querying absence records from {} to {} (total {} dates)", startDate, endDate, dates.size());
        
        if (employeeName != null) {
            // Query for specific employee
            Optional<Employee> employeeOpt = employees.stream()
                    .filter(emp -> emp.getName().equalsIgnoreCase(employeeName))
                    .findFirst();
            
            if (employeeOpt.isPresent()) {
                Employee employee = employeeOpt.get();
                
                // Get all records for this employee in the date range
                for (LocalDate date : dates) {
                    Optional<AbsenceRecord> record = absenceRecordRepository
                            .findByEmployeeIdAndAbsenceDate(employee.getId(), date);
                    
                    if (record.isPresent()) {
                        String recordStatus = record.get().getAbsenceType().name();
                        logger.debug("Found record for {} on {}: {}", employeeName, date, recordStatus);
                        if (statusFilter.contains("ALL") || statusFilter.contains(recordStatus)) {
                            results.add(record.get());
                        }
                    } else if (statusFilter.contains("ALL") || statusFilter.contains("P")) {
                        // No record means present - create a virtual record for display
                        logger.debug("No record found for {} on {} - assuming present", employeeName, date);
                        AbsenceRecord virtualRecord = new AbsenceRecord();
                        virtualRecord.setEmployee(employee);
                        virtualRecord.setAbsenceDate(date);
                        virtualRecord.setAbsenceType(AbsenceRecord.AbsenceType.P);
                        virtualRecord.setReason("Present");
                        results.add(virtualRecord);
                    }
                }
            } else {
                logger.warn("Employee not found: {}", employeeName);
            }
        } else {
            // Query for all employees in the date range - use optimized query
            List<AbsenceRecord> allRecords;
            
            if (statusFilter.contains("ALL")) {
                allRecords = absenceRecordRepository.findByAbsenceDateBetween(startDate, endDate);
            } else {
                // Convert status filter to AbsenceType enum
                List<AbsenceRecord.AbsenceType> absenceTypes = statusFilter.stream()
                        .filter(status -> !status.equals("P")) // Exclude Present as it's not stored
                        .map(AbsenceRecord.AbsenceType::valueOf)
                        .collect(Collectors.toList());
                
                if (!absenceTypes.isEmpty()) {
                    allRecords = absenceRecordRepository.findByAbsenceDateBetweenAndAbsenceTypeIn(
                            startDate, endDate, absenceTypes);
                } else {
                    allRecords = new ArrayList<>();
                }
            }
            
            logger.info("Found {} absence records in date range {} to {}", allRecords.size(), startDate, endDate);
            
            // Filter records to only include the specific dates requested
            Set<LocalDate> requestedDates = new HashSet<>(dates);
            for (AbsenceRecord record : allRecords) {
                if (requestedDates.contains(record.getAbsenceDate())) {
                    String recordStatus = record.getAbsenceType().name();
                    if (statusFilter.contains("ALL") || statusFilter.contains(recordStatus)) {
                        logger.debug("Adding record: {} - {} - {}", 
                            record.getEmployee().getName(), record.getAbsenceDate(), recordStatus);
                        results.add(record);
                    }
                }
            }
            
            // If looking for present employees, add those without records for each requested date
            if (statusFilter.contains("ALL") || statusFilter.contains("P")) {
                for (LocalDate date : dates) {
                    Set<Long> absentEmployeeIds = allRecords.stream()
                            .filter(record -> record.getAbsenceDate().equals(date))
                            .map(record -> record.getEmployee().getId())
                            .collect(Collectors.toSet());
                    
                    for (Employee employee : employees) {
                        if (!absentEmployeeIds.contains(employee.getId())) {
                            logger.debug("Adding present record for: {} on {}", employee.getName(), date);
                            AbsenceRecord virtualRecord = new AbsenceRecord();
                            virtualRecord.setEmployee(employee);
                            virtualRecord.setAbsenceDate(date);
                            virtualRecord.setAbsenceType(AbsenceRecord.AbsenceType.P);
                            virtualRecord.setReason("Present");
                            results.add(virtualRecord);
                        }
                    }
                }
            }
        }
        
        logger.info("Query completed. Found {} total records", results.size());
        return results;
    }
    
    /**
     * Build a human-readable response for query results
     */
    private String buildQueryResponse(List<AbsenceRecord> records, List<LocalDate> dates, 
                                    List<String> statusFilter, String queryType, String employeeName) {
        logger.info("Building query response for {} records, {} dates, statusFilter: {}", 
            records.size(), dates.size(), statusFilter);
        
        // Filter out present records if we're looking for absences/vacations only
        List<AbsenceRecord> relevantRecords = records.stream()
                .filter(record -> {
                    String status = record.getAbsenceType().name();
                    boolean isRelevant = statusFilter.contains("ALL") || statusFilter.contains(status);
                    // For absence queries, exclude present records unless specifically requested
                    if (!statusFilter.contains("ALL") && !statusFilter.contains("P") && "P".equals(status)) {
                        isRelevant = false;
                    }
                    logger.debug("Record: {} - {} - {} -> relevant: {}", 
                        record.getEmployee().getName(), record.getAbsenceDate(), status, isRelevant);
                    return isRelevant;
                })
                .collect(Collectors.toList());
        
        logger.info("After filtering: {} relevant records", relevantRecords.size());
        
        if (relevantRecords.isEmpty()) {
            if (employeeName != null) {
                return String.format("Good news! %s was present on all the requested dates. 😊", employeeName);
            } else {
                // Check if we were looking for absences/vacations specifically
                if (statusFilter.contains("A") || statusFilter.contains("V")) {
                    return "Great! No one was absent or on vacation during the requested period. Everyone was present! 🎉";
                } else {
                    return "No records found for the requested criteria.";
                }
            }
        }
        
        StringBuilder response = new StringBuilder();
        
        if (dates.size() == 1) {
            // Single date query
            LocalDate date = dates.get(0);
            String dateStr = date.format(DateTimeFormatter.ofPattern("MMMM d, yyyy"));
            
            Map<AbsenceRecord.AbsenceType, List<AbsenceRecord>> groupedByStatus = relevantRecords.stream()
                    .collect(Collectors.groupingBy(AbsenceRecord::getAbsenceType));
            
            response.append(String.format("Here's the attendance for %s:\n\n", dateStr));
            
            if (groupedByStatus.containsKey(AbsenceRecord.AbsenceType.A)) {
                List<String> absentNames = groupedByStatus.get(AbsenceRecord.AbsenceType.A).stream()
                        .map(r -> r.getEmployee().getName())
                        .collect(Collectors.toList());
                response.append(String.format("😷 Absent (%d): %s\n", absentNames.size(), String.join(", ", absentNames)));
            }
            
            if (groupedByStatus.containsKey(AbsenceRecord.AbsenceType.V)) {
                List<String> vacationNames = groupedByStatus.get(AbsenceRecord.AbsenceType.V).stream()
                        .map(r -> r.getEmployee().getName())
                        .collect(Collectors.toList());
                response.append(String.format("🏖️ On Vacation (%d): %s\n", vacationNames.size(), String.join(", ", vacationNames)));
            }
            
            if (groupedByStatus.containsKey(AbsenceRecord.AbsenceType.P)) {
                List<String> presentNames = groupedByStatus.get(AbsenceRecord.AbsenceType.P).stream()
                        .map(r -> r.getEmployee().getName())
                        .collect(Collectors.toList());
                if (!presentNames.isEmpty() && (statusFilter.contains("ALL") || statusFilter.contains("P"))) {
                    response.append(String.format("✅ Present (%d): %s\n", presentNames.size(), String.join(", ", presentNames)));
                }
            }
        } else {
            // Multiple dates query - group by employee and show their absence/vacation days
            response.append("Here's the attendance summary:\n\n");
            
            Map<String, List<AbsenceRecord>> groupedByEmployee = relevantRecords.stream()
                    .collect(Collectors.groupingBy(r -> r.getEmployee().getName()));
            
            if (groupedByEmployee.isEmpty()) {
                response.append("No absences or vacations found during this period. 🎉\n");
            } else {
                for (Map.Entry<String, List<AbsenceRecord>> entry : groupedByEmployee.entrySet()) {
                    String empName = entry.getKey();
                    List<AbsenceRecord> empRecords = entry.getValue();
                    
                    response.append(String.format("👤 %s:\n", empName));
                    for (AbsenceRecord record : empRecords) {
                        String dateStr = record.getAbsenceDate().format(DateTimeFormatter.ofPattern("MMM d"));
                        String statusEmoji = getStatusEmoji(record.getAbsenceType());
                        String statusText = getStatusText(record.getAbsenceType());
                        response.append(String.format("   %s %s - %s\n", statusEmoji, dateStr, statusText));
                    }
                    response.append("\n");
                }
            }
        }
        
        return response.toString().trim();
    }
    
    /**
     * Find the closest employee name using simple string matching
     */
    private String findClosestEmployeeName(String input, List<Employee> employees) {
        String lowerInput = input.toLowerCase();
        
        // First try exact substring match
        for (Employee employee : employees) {
            String lowerName = employee.getName().toLowerCase();
            if (lowerName.contains(lowerInput) || lowerInput.contains(lowerName)) {
                return employee.getName();
            }
        }
        
        // Then try first name match and partial matches
        String[] inputParts = lowerInput.split("\\s+");
        for (Employee employee : employees) {
            String[] nameParts = employee.getName().toLowerCase().split("\\s+");
            for (String inputPart : inputParts) {
                for (String namePart : nameParts) {
                    // Check if input part starts with name part or vice versa
                    if (namePart.startsWith(inputPart) || inputPart.startsWith(namePart)) {
                        return employee.getName();
                    }
                    // Check for common abbreviations (Jon -> John)
                    if ((inputPart.equals("jon") && namePart.startsWith("john")) ||
                        (inputPart.startsWith("john") && namePart.equals("jon"))) {
                        return employee.getName();
                    }
                    // Check for similar length and similar characters
                    if (Math.abs(inputPart.length() - namePart.length()) <= 2 && 
                        calculateSimilarity(inputPart, namePart) > 0.6) {
                        return employee.getName();
                    }
                }
            }
        }
        
        return null; // No close match found
    }
    
    /**
     * Calculate similarity between two strings using simple character matching
     */
    private double calculateSimilarity(String s1, String s2) {
        if (s1.length() == 0 || s2.length() == 0) {
            return 0.0;
        }
        
        int matches = 0;
        int minLength = Math.min(s1.length(), s2.length());
        
        for (int i = 0; i < minLength; i++) {
            if (s1.charAt(i) == s2.charAt(i)) {
                matches++;
            }
        }
        
        return (double) matches / Math.max(s1.length(), s2.length());
    }
    
    /**
     * Convert AbsenceRecord to Map for JSON serialization
     */
    private Map<String, Object> convertAbsenceRecordToMap(AbsenceRecord record) {
        Map<String, Object> map = new HashMap<>();
        map.put("employeeName", record.getEmployee().getName());
        map.put("employeeId", record.getEmployee().getId());
        map.put("date", record.getAbsenceDate().toString());
        map.put("status", record.getAbsenceType().name());
        map.put("reason", record.getReason());
        return map;
    }
    
    /**
     * Get human-readable status text
     */
    private String getStatusText(AbsenceRecord.AbsenceType absenceType) {
        switch (absenceType) {
            case A: return "absent";
            case V: return "on vacation";
            case P: return "present";
            default: return absenceType.name().toLowerCase();
        }
    }
    
    /**
     * Get emoji for status
     */
    private String getStatusEmoji(AbsenceRecord.AbsenceType absenceType) {
        switch (absenceType) {
            case A: return "😷";
            case V: return "🏖️";
            case P: return "✅";
            default: return "❓";
        }
    }
    
    /**
     * Get emoji for status
     */
    private String getStatusEmoji(String status) {
        switch (status.toUpperCase()) {
            case "A": return "😷";
            case "V": return "🏖️";
            case "P": return "✅";
            default: return "❓";
        }
    }
    
    /**
     * Format dates for response text
     */
    private String formatDatesForResponse(List<LocalDate> dates) {
        if (dates.size() == 1) {
            return dates.get(0).format(DateTimeFormatter.ofPattern("MMMM d, yyyy"));
        } else if (dates.size() == 2) {
            return String.format("%s and %s", 
                    dates.get(0).format(DateTimeFormatter.ofPattern("MMMM d")),
                    dates.get(1).format(DateTimeFormatter.ofPattern("MMMM d, yyyy")));
        } else {
            return String.format("%d dates", dates.size());
        }
    }
    
    /**
     * Handle errors and return user-friendly error responses with chatbot personality
     */
    private Mono<ChatResponseDTO> handleError(Throwable error, String conversationId) {
        logger.error("Error in AI service for conversation {}: {}", conversationId, error.getMessage(), error);
        
        String errorMessage = generateUserFriendlyErrorMessage(error);
        
        // Add error message to conversation history for context
        try {
            conversationContextService.addAssistantMessage(conversationId, errorMessage);
        } catch (Exception e) {
            logger.warn("Failed to add error message to conversation history for {}: {}", conversationId, e.getMessage());
        }
        
        return Mono.just(ChatResponseDTO.error(errorMessage, conversationId));
    }
    
    /**
     * Generate user-friendly error messages with chatbot personality
     */
    private String generateUserFriendlyErrorMessage(Throwable error) {
        if (error instanceof GeminiAPIService.GeminiAPIException) {
            GeminiAPIService.GeminiAPIException geminiError = (GeminiAPIService.GeminiAPIException) error;
            
            if (geminiError.getStatusCode() == 429) {
                return "Whoa! I'm getting a bit overwhelmed with requests right now. 😅 Give me a moment to catch my breath and try again!";
            } else if (geminiError.getStatusCode() == 401 || geminiError.getStatusCode() == 403) {
                logger.error("Authentication/Authorization error with Gemini API - check API key configuration");
                return "Oops! I seem to have lost my credentials. 🔑 Please contact your administrator - there might be a configuration issue!";
            } else if (geminiError.getStatusCode() >= 500) {
                return "My AI brain is having a temporary hiccup! 🤖 The service seems to be down. Please try again in a few minutes!";
            } else {
                return "I'm having trouble connecting to my AI brain right now. 🤖 Please try again in a moment!";
            }
        } else if (error instanceof java.util.concurrent.TimeoutException || 
                   error.getCause() instanceof java.util.concurrent.TimeoutException) {
            return "Hmm, I'm thinking really hard about your request but it's taking longer than usual! 🤔 Please try again - I promise to be faster next time!";
        } else if (error instanceof java.net.ConnectException || 
                   error.getCause() instanceof java.net.ConnectException) {
            return "I can't seem to reach my AI brain right now - there might be a network issue! 📡 Please try again in a moment!";
        } else if (error instanceof com.fasterxml.jackson.core.JsonProcessingException) {
            logger.warn("JSON parsing error in AI service: {}", error.getMessage());
            return "I got a bit confused trying to understand the response! 😵‍💫 Let me try that again - please repeat your request!";
        } else if (error instanceof IllegalArgumentException) {
            logger.warn("Invalid argument in AI service: {}", error.getMessage());
            return "I think there might be something wrong with your request format. 🤷‍♂️ Could you try rephrasing that?";
        } else if (error instanceof NullPointerException) {
            logger.error("Null pointer exception in AI service - this shouldn't happen!", error);
            return "Oops! I encountered an unexpected issue. 😅 Please try again, and if this keeps happening, let your administrator know!";
        } else {
            // Generic fallback with some personality
            String[] fallbackMessages = {
                "Something unexpected happened on my end! 😅 Please try again!",
                "I hit a snag while processing your request! 🐛 Give it another shot!",
                "Whoops! I stumbled a bit there. 🤪 Please try your request again!",
                "I'm having a moment here! 🤦‍♂️ Please try again and I'll do better!",
                "Technical difficulties on my end! 🔧 Please give it another try!"
            };
            
            // Use a simple hash to pick a consistent message for similar errors
            int index = Math.abs(error.getClass().getSimpleName().hashCode()) % fallbackMessages.length;
            return fallbackMessages[index];
        }
    }
}