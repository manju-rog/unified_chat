package com.companyname.absence_management.services;

import com.companyname.absence_management.config.AIConfig;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Service
public class GeminiAPIService {
    
    private static final Logger logger = LoggerFactory.getLogger(GeminiAPIService.class);
    
    private final WebClient webClient;
    private final AIConfig aiConfig;
    private final ObjectMapper objectMapper;
    
    @Autowired
    public GeminiAPIService(AIConfig aiConfig, ObjectMapper objectMapper) {
        this.aiConfig = aiConfig;
        this.objectMapper = objectMapper;
        this.webClient = WebClient.builder()
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .build();
    }
    
    public Mono<GeminiResponse> callGeminiAPI(String systemPrompt, String userInput, List<String> conversationHistory) {
        logger.info("Calling Gemini API");
        
        try {
            if (systemPrompt == null || systemPrompt.trim().isEmpty()) {
                return Mono.error(new IllegalArgumentException("System prompt cannot be null or empty"));
            }
            
            if (userInput == null || userInput.trim().isEmpty()) {
                return Mono.error(new IllegalArgumentException("User input cannot be null or empty"));
            }
            
            if (aiConfig.getGemini().getApiKey() == null || aiConfig.getGemini().getApiKey().trim().isEmpty()) {
                return Mono.error(new GeminiAPIException("Gemini API key is not configured", 500));
            }
            
            if (aiConfig.getGemini().getApiUrl() == null || aiConfig.getGemini().getApiUrl().trim().isEmpty()) {
                return Mono.error(new GeminiAPIException("Gemini API URL is not configured", 500));
            }
            
            ObjectNode requestBody;
            try {
                requestBody = createGeminiRequest(systemPrompt, userInput, conversationHistory);
            } catch (Exception e) {
                logger.error("Failed to create Gemini API request body: {}", e.getMessage());
                return Mono.error(new GeminiAPIException("Failed to create API request", 500));
            }
            
            String apiUrl = aiConfig.getGemini().getApiUrl() + "?key=" + aiConfig.getGemini().getApiKey();
            int timeoutSeconds = aiConfig.getGemini().getTimeoutSeconds();
            
            return webClient.post()
                    .uri(apiUrl)
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .doOnError(error -> logger.error("Error during Gemini API call: {}", error.getMessage()))
                    .map(this::parseGeminiResponse)
                    .map(response -> validateAndConvertResponse(response, userInput))
                    .onErrorMap(this::handleGeminiError);
                    
        } catch (Exception e) {
            logger.error("Unexpected error creating Gemini API request: {}", e.getMessage());
            return Mono.error(new GeminiAPIException("Failed to create Gemini API request: " + e.getMessage(), 500));
        }
    }
    
    /**
     * Create the request body for Gemini API
     */
    private ObjectNode createGeminiRequest(String systemPrompt, String userInput, List<String> conversationHistory) {
        ObjectNode requestBody = objectMapper.createObjectNode();
        
        // Create contents array
        ArrayNode contents = objectMapper.createArrayNode();
        ObjectNode content = objectMapper.createObjectNode();
        ArrayNode parts = objectMapper.createArrayNode();
        
        // Build the full prompt with context
        StringBuilder fullPrompt = new StringBuilder(systemPrompt);
        
        if (conversationHistory != null && !conversationHistory.isEmpty()) {
            fullPrompt.append("\n\nRecent conversation:\n");
            for (String message : conversationHistory) {
                fullPrompt.append(message).append("\n");
            }
        }
        
        fullPrompt.append("\n\nUser request: ").append(userInput);
        
        ObjectNode textPart = objectMapper.createObjectNode();
        textPart.put("text", fullPrompt.toString());
        parts.add(textPart);
        
        content.set("parts", parts);
        contents.add(content);
        requestBody.set("contents", contents);
        
        // Add function definitions
        ArrayNode tools = objectMapper.createArrayNode();
        ObjectNode tool = objectMapper.createObjectNode();
        ArrayNode functionDeclarations = objectMapper.createArrayNode();
        
        // Add markAbsence function
        functionDeclarations.add(createMarkAbsenceFunction());
        
        // Add queryAbsence function
        functionDeclarations.add(createQueryAbsenceFunction());
        
        tool.set("functionDeclarations", functionDeclarations);
        tools.add(tool);
        requestBody.set("tools", tools);
        
        // Add generation config with function call enforcement
        ObjectNode generationConfig = objectMapper.createObjectNode();
        generationConfig.put("temperature", 0.1); // Lower temperature for more deterministic function calls
        generationConfig.put("topK", 20);
        generationConfig.put("topP", 0.7);
        generationConfig.put("maxOutputTokens", 1000);
        requestBody.set("generationConfig", generationConfig);
        
        // Add tool config to force function calls for absence operations
        ObjectNode toolConfig = objectMapper.createObjectNode();
        ObjectNode functionCallingConfig = objectMapper.createObjectNode();
        functionCallingConfig.put("mode", "ANY"); // Force function calls when tools are available
        toolConfig.set("functionCallingConfig", functionCallingConfig);
        requestBody.set("toolConfig", toolConfig);
        
        return requestBody;
    }
    
    /**
     * Create the markAbsence function definition
     */
    private ObjectNode createMarkAbsenceFunction() {
        ObjectNode function = objectMapper.createObjectNode();
        function.put("name", "markAbsence");
        function.put("description", "REQUIRED: Use this function for ANY request to mark, set, or change employee attendance status. Examples: 'Mark John absent', 'Set Mary as present', 'John is on vacation today'. NEVER respond with text for these operations - ALWAYS use this function.");
        
        ObjectNode parameters = objectMapper.createObjectNode();
        parameters.put("type", "object");
        
        ObjectNode properties = objectMapper.createObjectNode();
        
        // employeeName property
        ObjectNode employeeName = objectMapper.createObjectNode();
        employeeName.put("type", "string");
        employeeName.put("description", "Full name of the employee (must match exactly from the available employees list)");
        properties.set("employeeName", employeeName);
        
        // dates property
        ObjectNode dates = objectMapper.createObjectNode();
        dates.put("type", "array");
        ObjectNode dateItems = objectMapper.createObjectNode();
        dateItems.put("type", "string");
        dates.set("items", dateItems);
        dates.put("description", "Array of dates in YYYY-MM-DD format");
        properties.set("dates", dates);
        
        // status property
        ObjectNode status = objectMapper.createObjectNode();
        status.put("type", "string");
        ArrayNode statusEnum = objectMapper.createArrayNode();
        statusEnum.add("P");
        statusEnum.add("A");
        statusEnum.add("V");
        status.set("enum", statusEnum);
        status.put("description", "Attendance status: P for Present, A for Absent, V for Vacation");
        properties.set("status", status);
        
        parameters.set("properties", properties);
        
        ArrayNode required = objectMapper.createArrayNode();
        required.add("employeeName");
        required.add("dates");
        required.add("status");
        parameters.set("required", required);
        
        function.set("parameters", parameters);
        
        return function;
    }
    
    /**
     * Create the queryAbsence function definition
     */
    private ObjectNode createQueryAbsenceFunction() {
        ObjectNode function = objectMapper.createObjectNode();
        function.put("name", "queryAbsence");
        function.put("description", "REQUIRED: Use this function for ANY request to query, check, or display attendance information. Examples: 'Who was absent?', 'Show me absences', 'List vacation days', 'Check John's attendance'. NEVER respond with text for these operations - ALWAYS use this function.");
        
        ObjectNode parameters = objectMapper.createObjectNode();
        parameters.put("type", "object");
        
        ObjectNode properties = objectMapper.createObjectNode();
        
        // queryType property
        ObjectNode queryType = objectMapper.createObjectNode();
        queryType.put("type", "string");
        ArrayNode queryTypeEnum = objectMapper.createArrayNode();
        queryTypeEnum.add("byDate");
        queryTypeEnum.add("byEmployee");
        queryTypeEnum.add("byDateRange");
        queryTypeEnum.add("byMonth");
        queryType.set("enum", queryTypeEnum);
        queryType.put("description", "Type of query: byDate for specific date, byEmployee for specific employee, byDateRange for date range, byMonth for entire month");
        properties.set("queryType", queryType);
        
        // dates property
        ObjectNode dates = objectMapper.createObjectNode();
        dates.put("type", "array");
        ObjectNode dateItems = objectMapper.createObjectNode();
        dateItems.put("type", "string");
        dates.set("items", dateItems);
        dates.put("description", "Array of dates in YYYY-MM-DD format to query. For month queries like 'August 2025', you MUST include ALL dates in that month (2025-08-01, 2025-08-02, ..., 2025-08-31). For single date queries, include just that date. CRITICAL: Month queries require ALL dates in the month to work properly.");
        properties.set("dates", dates);
        
        // employeeName property
        ObjectNode employeeName = objectMapper.createObjectNode();
        employeeName.put("type", "string");
        employeeName.put("description", "Employee name to query (optional, only for byEmployee queries)");
        properties.set("employeeName", employeeName);
        
        // statusFilter property
        ObjectNode statusFilter = objectMapper.createObjectNode();
        statusFilter.put("type", "array");
        ObjectNode statusItems = objectMapper.createObjectNode();
        statusItems.put("type", "string");
        ArrayNode statusEnum = objectMapper.createArrayNode();
        statusEnum.add("A");
        statusEnum.add("V");
        statusEnum.add("P");
        statusEnum.add("ALL");
        statusItems.set("enum", statusEnum);
        statusFilter.set("items", statusItems);
        statusFilter.put("description", "Filter by status: A for Absent, V for Vacation, P for Present, ALL for all statuses. Default is A and V for absence queries, ALL for individual employee queries.");
        properties.set("statusFilter", statusFilter);
        
        // monthYear property
        ObjectNode monthYear = objectMapper.createObjectNode();
        monthYear.put("type", "string");
        monthYear.put("description", "Month and year in YYYY-MM format (optional, for month-based queries like \"August 2025\" = \"2025-08\")");
        properties.set("monthYear", monthYear);
        
        parameters.set("properties", properties);
        
        ArrayNode required = objectMapper.createArrayNode();
        required.add("queryType");
        required.add("dates");
        parameters.set("required", required);
        
        function.set("parameters", parameters);
        
        return function;
    }
    
    /**
     * Validate and potentially convert text responses to function calls
     */
    private GeminiResponse validateAndConvertResponse(GeminiResponse response, String userInput) {
        // If we got a function call, we're good
        if (response.getType() == GeminiResponse.ResponseType.FUNCTION_CALL) {
            logger.info("Function call received as expected: {}", response.getFunctionName());
            return response;
        }
        
        // If we got text, check if it's an absence-related request that should have been a function call
        if (response.getType() == GeminiResponse.ResponseType.TEXT) {
            String textResponse = response.getText();
            
            // Check if this looks like an absence operation that should have been a function call
            if (isAbsenceOperation(userInput)) {
                logger.warn("Received text response for absence operation. Attempting to convert to function call.");
                logger.debug("User input: {}", userInput);
                logger.debug("Text response: {}", textResponse);
                
                // Try to extract function call from text response
                GeminiResponse convertedResponse = attemptTextToFunctionConversion(userInput, textResponse);
                if (convertedResponse != null) {
                    logger.info("Successfully converted text response to function call: {}", convertedResponse.getFunctionName());
                    return convertedResponse;
                }
                
                // If conversion failed, return an error response
                logger.error("Failed to convert text response to function call for absence operation");
                return new GeminiResponse(GeminiResponse.ResponseType.TEXT, 
                    "I understand you want to work with employee absences, but I'm having trouble processing your request right now. Could you please try rephrasing it? For example: 'Mark John absent today' or 'Who was absent yesterday?'", 
                    null, null);
            }
            
            // For non-absence operations, text responses are fine
            logger.debug("Text response for non-absence operation is acceptable");
            return response;
        }
        
        return response;
    }
    
    /**
     * Check if the user input is an absence-related operation
     */
    private boolean isAbsenceOperation(String userInput) {
        if (userInput == null) return false;
        
        String input = userInput.toLowerCase();
        
        // Keywords that indicate absence marking operations
        String[] markingKeywords = {"mark", "set", "make", "put", "absent", "present", "vacation", "holiday"};
        
        // Keywords that indicate absence query operations  
        String[] queryKeywords = {"who", "show", "list", "find", "get", "absent", "vacation", "present", "was", "were", "is", "are"};
        
        // Check for marking operations
        for (String keyword : markingKeywords) {
            if (input.contains(keyword)) {
                return true;
            }
        }
        
        // Check for query operations
        for (String keyword : queryKeywords) {
            if (input.contains(keyword)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Attempt to convert text response to function call based on user input
     */
    private GeminiResponse attemptTextToFunctionConversion(String userInput, String textResponse) {
        try {
            String input = userInput.toLowerCase();
            
            // Try to extract employee name from input
            String employeeName = extractEmployeeName(userInput);
            if (employeeName == null) {
                logger.warn("Could not extract employee name from input: {}", userInput);
                return null;
            }
            
            // Try to extract dates
            List<String> dates = extractDates(userInput);
            if (dates.isEmpty()) {
                // Default to today if no date specified
                dates.add(LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE));
            }
            
            // Determine if this is a marking or query operation
            if (isMarkingOperation(input)) {
                // Extract status
                String status = extractStatus(input);
                if (status == null) {
                    logger.warn("Could not extract status from marking operation: {}", userInput);
                    return null;
                }
                
                // Create markAbsence function call
                ObjectNode args = objectMapper.createObjectNode();
                args.put("employeeName", employeeName);
                ArrayNode datesArray = objectMapper.createArrayNode();
                dates.forEach(datesArray::add);
                args.set("dates", datesArray);
                args.put("status", status);
                
                return new GeminiResponse(GeminiResponse.ResponseType.FUNCTION_CALL, null, "markAbsence", args);
                
            } else if (isQueryOperation(input)) {
                // Create queryAbsence function call
                ObjectNode args = objectMapper.createObjectNode();
                args.put("queryType", "byEmployee");
                ArrayNode datesArray = objectMapper.createArrayNode();
                dates.forEach(datesArray::add);
                args.set("dates", datesArray);
                args.put("employeeName", employeeName);
                
                ArrayNode statusFilter = objectMapper.createArrayNode();
                statusFilter.add("ALL");
                args.set("statusFilter", statusFilter);
                
                return new GeminiResponse(GeminiResponse.ResponseType.FUNCTION_CALL, null, "queryAbsence", args);
            }
            
        } catch (Exception e) {
            logger.error("Error converting text to function call: {}", e.getMessage(), e);
        }
        
        return null;
    }
    
    /**
     * Check if input is a marking operation
     */
    private boolean isMarkingOperation(String input) {
        return input.contains("mark") || input.contains("set") || input.contains("make") || input.contains("put");
    }
    
    /**
     * Check if input is a query operation
     */
    private boolean isQueryOperation(String input) {
        return input.contains("who") || input.contains("show") || input.contains("list") || 
               input.contains("find") || input.contains("get") || input.contains("was") || 
               input.contains("were") || input.contains("is") || input.contains("are");
    }
    
    /**
     * Extract employee name from user input
     */
    private String extractEmployeeName(String input) {
        // Simple pattern matching for common employee names
        // This is a basic implementation - could be enhanced with NLP
        
        String[] commonNames = {"john", "jane", "bob", "alice", "mike", "sarah", "david", "lisa", "tom", "mary"};
        String inputLower = input.toLowerCase();
        
        for (String name : commonNames) {
            if (inputLower.contains(name)) {
                // Capitalize first letter
                return name.substring(0, 1).toUpperCase() + name.substring(1);
            }
        }
        
        // Try to extract name patterns (word after "mark" or before "absent/present/vacation")
        String[] words = input.split("\\s+");
        for (int i = 0; i < words.length; i++) {
            String word = words[i].toLowerCase();
            if (word.equals("mark") && i + 1 < words.length) {
                String nextWord = words[i + 1];
                if (!nextWord.toLowerCase().matches("(absent|present|vacation|as|him|her|them)")) {
                    return capitalizeFirstLetter(nextWord);
                }
            }
        }
        
        return null;
    }
    
    /**
     * Extract status from user input
     */
    private String extractStatus(String input) {
        String inputLower = input.toLowerCase();
        
        if (inputLower.contains("absent")) return "A";
        if (inputLower.contains("present")) return "P";
        if (inputLower.contains("vacation") || inputLower.contains("holiday")) return "V";
        
        return null;
    }
    
    /**
     * Extract dates from user input
     */
    private List<String> extractDates(String input) {
        List<String> dates = new ArrayList<>();
        String inputLower = input.toLowerCase();
        LocalDate today = LocalDate.now();
        
        if (inputLower.contains("today")) {
            dates.add(today.format(DateTimeFormatter.ISO_LOCAL_DATE));
        } else if (inputLower.contains("tomorrow")) {
            dates.add(today.plusDays(1).format(DateTimeFormatter.ISO_LOCAL_DATE));
        } else if (inputLower.contains("yesterday")) {
            dates.add(today.minusDays(1).format(DateTimeFormatter.ISO_LOCAL_DATE));
        }
        
        return dates;
    }
    
    /**
     * Capitalize first letter of a word
     */
    private String capitalizeFirstLetter(String word) {
        if (word == null || word.isEmpty()) return word;
        return word.substring(0, 1).toUpperCase() + word.substring(1).toLowerCase();
    }

    /**
     * Parse the Gemini API response
     */
    private GeminiResponse parseGeminiResponse(String responseBody) {
        logger.debug("Parsing Gemini API response - Length: {}", responseBody.length());
        
        try {
            if (responseBody == null || responseBody.trim().isEmpty()) {
                logger.error("Received null or empty response body from Gemini API");
                throw new GeminiAPIException("Empty response from Gemini API", 500);
            }
            
            JsonNode root;
            try {
                root = objectMapper.readTree(responseBody);
            } catch (Exception e) {
                logger.error("Failed to parse JSON response from Gemini API: {}", e.getMessage());
                logger.debug("Invalid JSON response body: {}", responseBody);
                throw new GeminiAPIException("Invalid JSON response from Gemini API", 500);
            }
            
            // Check for API error in response
            if (root.has("error")) {
                JsonNode error = root.get("error");
                String errorMessage = error.has("message") ? error.get("message").asText() : "Unknown API error";
                int errorCode = error.has("code") ? error.get("code").asInt() : 500;
                
                logger.error("Gemini API returned error: {} (Code: {})", errorMessage, errorCode);
                throw new GeminiAPIException("Gemini API error: " + errorMessage, errorCode);
            }
            
            if (!root.has("candidates")) {
                logger.error("No 'candidates' field in Gemini API response");
                logger.debug("Response structure: {}", root.toString());
                throw new GeminiAPIException("Invalid response structure: missing candidates", 500);
            }
            
            JsonNode candidates = root.get("candidates");
            if (!candidates.isArray() || candidates.isEmpty()) {
                logger.error("Candidates field is empty or not an array");
                throw new GeminiAPIException("No response candidates from Gemini API", 500);
            }
            
            JsonNode candidate = candidates.get(0);
            
            // Check if the candidate was blocked or filtered
            if (candidate.has("finishReason")) {
                String finishReason = candidate.get("finishReason").asText();
                if ("SAFETY".equals(finishReason)) {
                    logger.warn("Gemini API response was blocked due to safety filters");
                    throw new GeminiAPIException("Response was blocked by safety filters", 400);
                } else if ("RECITATION".equals(finishReason)) {
                    logger.warn("Gemini API response was blocked due to recitation");
                    throw new GeminiAPIException("Response was blocked due to recitation", 400);
                }
            }
            
            if (!candidate.has("content")) {
                logger.error("No 'content' field in candidate");
                logger.debug("Candidate structure: {}", candidate.toString());
                throw new GeminiAPIException("Invalid candidate structure: missing content", 500);
            }
            
            JsonNode content = candidate.get("content");
            if (!content.has("parts")) {
                logger.error("No 'parts' field in content");
                logger.debug("Content structure: {}", content.toString());
                throw new GeminiAPIException("Invalid content structure: missing parts", 500);
            }
            
            JsonNode parts = content.get("parts");
            if (!parts.isArray() || parts.isEmpty()) {
                logger.error("Parts field is empty or not an array");
                throw new GeminiAPIException("Invalid parts structure", 500);
            }
            
            for (JsonNode part : parts) {
                // Check for function call
                if (part.has("functionCall")) {
                    JsonNode functionCall = part.get("functionCall");
                    
                    if (!functionCall.has("name")) {
                        logger.error("Function call missing name field");
                        throw new GeminiAPIException("Invalid function call: missing name", 500);
                    }
                    
                    String functionName = functionCall.get("name").asText();
                    JsonNode args = functionCall.has("args") ? functionCall.get("args") : objectMapper.createObjectNode();
                    
                    logger.info("Parsed function call: {} with {} arguments", functionName, args.size());
                    logger.debug("Function call arguments: {}", args.toString());
                    
                    return new GeminiResponse(GeminiResponse.ResponseType.FUNCTION_CALL, null, functionName, args);
                }
                
                // Check for text response
                if (part.has("text")) {
                    String text = part.get("text").asText();
                    
                    if (text == null) {
                        logger.warn("Text field is null in response part");
                        text = "";
                    }
                    
                    logger.info("Parsed text response - Length: {}", text.length());
                    logger.debug("Text response content: {}", text);
                    
                    return new GeminiResponse(GeminiResponse.ResponseType.TEXT, text, null, null);
                }
            }
            
            logger.error("No valid response content found in any part");
            logger.debug("Parts content: {}", parts.toString());
            throw new GeminiAPIException("No valid response content found", 500);
            
        } catch (GeminiAPIException e) {
            // Re-throw our custom exceptions
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error parsing Gemini API response: {}", e.getMessage(), e);
            logger.debug("Response body that caused error: {}", responseBody);
            throw new GeminiAPIException("Failed to parse Gemini API response: " + e.getMessage(), 500);
        }
    }
    
    /**
     * Handle errors from Gemini API calls
     */
    private Throwable handleGeminiError(Throwable error) {
        logger.debug("Handling Gemini API error: {}", error.getClass().getSimpleName());
        
        if (error instanceof GeminiAPIException) {
            // Already a GeminiAPIException, just return it
            return error;
        }
        
        if (error instanceof WebClientResponseException) {
            WebClientResponseException webError = (WebClientResponseException) error;
            String errorBody = webError.getResponseBodyAsString();
            int statusCode = webError.getStatusCode().value();
            
            logger.error("Gemini API HTTP error: {} - Body: {}", statusCode, errorBody);
            
            // Parse error message if possible
            String errorMessage = "HTTP " + statusCode;
            try {
                if (errorBody != null && !errorBody.trim().isEmpty()) {
                    JsonNode errorJson = objectMapper.readTree(errorBody);
                    if (errorJson.has("error")) {
                        JsonNode errorNode = errorJson.get("error");
                        if (errorNode.has("message")) {
                            errorMessage = errorNode.get("message").asText();
                        } else if (errorNode.has("status")) {
                            errorMessage = errorNode.get("status").asText();
                        }
                    }
                }
            } catch (Exception e) {
                logger.warn("Could not parse error response from Gemini API: {}", e.getMessage());
            }
            
            // Provide more specific error messages based on status code
            switch (statusCode) {
                case 400:
                    logger.warn("Bad request to Gemini API: {}", errorMessage);
                    return new GeminiAPIException("Invalid request to Gemini API: " + errorMessage, statusCode);
                case 401:
                    logger.error("Authentication failed with Gemini API - check API key");
                    return new GeminiAPIException("Authentication failed - invalid API key", statusCode);
                case 403:
                    logger.error("Access forbidden to Gemini API - check permissions");
                    return new GeminiAPIException("Access forbidden - check API permissions", statusCode);
                case 429:
                    logger.warn("Rate limit exceeded for Gemini API");
                    return new GeminiAPIException("Rate limit exceeded - too many requests", statusCode);
                case 500:
                case 502:
                case 503:
                case 504:
                    logger.error("Gemini API server error: {}", statusCode);
                    return new GeminiAPIException("Gemini API server error: " + errorMessage, statusCode);
                default:
                    return new GeminiAPIException("Gemini API error: " + errorMessage, statusCode);
            }
        }
        
        if (error instanceof java.util.concurrent.TimeoutException) {
            logger.error("Timeout calling Gemini API after {} seconds", aiConfig.getGemini().getTimeoutSeconds());
            return new GeminiAPIException("Request to Gemini API timed out", 408);
        }
        
        if (error instanceof java.net.ConnectException) {
            logger.error("Connection failed to Gemini API: {}", error.getMessage());
            return new GeminiAPIException("Cannot connect to Gemini API", 503);
        }
        
        if (error instanceof java.net.UnknownHostException) {
            logger.error("Unknown host for Gemini API: {}", error.getMessage());
            return new GeminiAPIException("Cannot resolve Gemini API hostname", 503);
        }
        
        if (error instanceof javax.net.ssl.SSLException) {
            logger.error("SSL error connecting to Gemini API: {}", error.getMessage());
            return new GeminiAPIException("SSL connection error to Gemini API", 503);
        }
        
        // Check for reactor timeout
        if (error.getMessage() != null && error.getMessage().contains("timeout")) {
            logger.error("Reactor timeout calling Gemini API: {}", error.getMessage());
            return new GeminiAPIException("Request to Gemini API timed out", 408);
        }
        
        // Generic network/IO errors
        if (error instanceof java.io.IOException) {
            logger.error("IO error calling Gemini API: {}", error.getMessage());
            return new GeminiAPIException("Network error calling Gemini API: " + error.getMessage(), 503);
        }
        
        // Fallback for any other error
        logger.error("Unexpected error calling Gemini API: {}", error.getMessage(), error);
        return new GeminiAPIException("Unexpected error calling Gemini API: " + error.getMessage(), 500);
    }
    
    /**
     * Build system prompt with current context and STRICT function call enforcement
     */
    public String buildSystemPrompt(List<String> employeeNames) {
        LocalDate currentDate = LocalDate.now();
        int currentYear = currentDate.getYear();
        String currentDateStr = currentDate.format(DateTimeFormatter.ISO_LOCAL_DATE);
        String employeeNamesStr = String.join(", ", employeeNames);
        
        return String.format("""
            🚨 CRITICAL SYSTEM INSTRUCTION - READ CAREFULLY 🚨
            
            You are an AI assistant for an absence management system. Today's date is %s.
            
            ⚠️ ABSOLUTE REQUIREMENT - NO EXCEPTIONS:
            For ANY request about employee attendance, you MUST use the provided functions.
            You are STRICTLY FORBIDDEN from providing text responses for attendance operations.
            
            MANDATORY FUNCTION USAGE:
            - Marking attendance → MUST call markAbsence function
            - Querying attendance → MUST call queryAbsence function
            - NO TEXT RESPONSES for these operations - ONLY function calls
            
            👥 AVAILABLE EMPLOYEES: %s

            🔧 WHEN TO USE markAbsence FUNCTION (REQUIRED):
            - "Mark John absent today" → IMMEDIATELY call markAbsence
            - "Set Jane as present" → IMMEDIATELY call markAbsence  
            - "John is on vacation" → IMMEDIATELY call markAbsence
            - "Make Bob absent" → IMMEDIATELY call markAbsence
            - ANY request to change attendance status → IMMEDIATELY call markAbsence
            
            🔍 WHEN TO USE queryAbsence FUNCTION (REQUIRED):
            - "Who was absent?" → IMMEDIATELY call queryAbsence
            - "Show me absences" → IMMEDIATELY call queryAbsence
            - "List absent employees" → IMMEDIATELY call queryAbsence
            - "Check John's attendance" → IMMEDIATELY call queryAbsence
            - "Who was absent in August?" → IMMEDIATELY call queryAbsence with ALL August dates
            - "Show me August absences" → IMMEDIATELY call queryAbsence with ALL August dates
            - ANY request to view attendance data → IMMEDIATELY call queryAbsence
            
            🗓️ CRITICAL MONTH QUERY RULE:
            For month queries (e.g., "September 2025", "who was absent in September"):
            - You MUST include ALL dates in that month in the dates array
            - September 2025 = ["2025-09-01", "2025-09-02", "2025-09-03", ..., "2025-09-30"]
            - August 2025 = ["2025-08-01", "2025-08-02", ..., "2025-08-31"]
            - Current year is %d, so "September" means "September %d"
            - Do NOT use just one date for month queries - use ALL dates!
            
            📅 EXAMPLES OF CORRECT DATE ARRAYS:
            - "who was absent in September" → dates: ["2025-09-01", "2025-09-02", ..., "2025-09-30"]
            - "show me August absences" → dates: ["2025-08-01", "2025-08-02", ..., "2025-08-31"]
            - "who was absent yesterday" → dates: ["2025-09-04"] (single date)

            📋 FUNCTION PARAMETERS:
            Status codes: A=Absent, P=Present, V=Vacation
            Date format: YYYY-MM-DD (today = %s)
            
            🚫 ABSOLUTELY FORBIDDEN RESPONSES:
            - "I'll mark John as absent" (WRONG - call function instead)
            - "Let me check who was absent" (WRONG - call function instead)  
            - "I can help you mark attendance" (WRONG - call function instead)
            - Any explanatory text for attendance operations (WRONG)
            
            ✅ CORRECT BEHAVIOR EXAMPLES:
            User: "Mark John absent today"
            You: [Call markAbsence function with employeeName="John", dates=["%s"], status="A"]
            
            User: "Who was absent yesterday?"
            You: [Call queryAbsence function with queryType="byDate", dates=["yesterday-date"]]
            
            🎯 EXECUTION RULES:
            1. Detect attendance request → Call appropriate function IMMEDIATELY
            2. Do NOT explain what you're doing → Just call the function
            3. Do NOT ask for confirmation → Just call the function
            4. If employee name unclear → Use best match and call function
            5. If date unclear → Use reasonable default and call function
            6. For non-attendance topics → Brief redirect only
            
            REMEMBER: Your job is to EXECUTE functions, not explain them!
            """, 
            currentDateStr, employeeNamesStr, currentYear, currentYear, currentDateStr, currentDateStr);
    }
    
    /**
     * Response class for Gemini API responses
     */
    public static class GeminiResponse {
        public enum ResponseType {
            TEXT, FUNCTION_CALL
        }
        
        private final ResponseType type;
        private final String text;
        private final String functionName;
        private final JsonNode functionArgs;
        
        public GeminiResponse(ResponseType type, String text, String functionName, JsonNode functionArgs) {
            this.type = type;
            this.text = text;
            this.functionName = functionName;
            this.functionArgs = functionArgs;
        }
        
        public ResponseType getType() { return type; }
        public String getText() { return text; }
        public String getFunctionName() { return functionName; }
        public JsonNode getFunctionArgs() { return functionArgs; }
        
        public boolean isTextResponse() { return type == ResponseType.TEXT; }
        public boolean isFunctionCall() { return type == ResponseType.FUNCTION_CALL; }
    }
    
    /**
     * Custom exception for Gemini API errors
     */
    public static class GeminiAPIException extends RuntimeException {
        private final int statusCode;
        
        public GeminiAPIException(String message, int statusCode) {
            super(message);
            this.statusCode = statusCode;
        }
        
        public int getStatusCode() { return statusCode; }
    }
}