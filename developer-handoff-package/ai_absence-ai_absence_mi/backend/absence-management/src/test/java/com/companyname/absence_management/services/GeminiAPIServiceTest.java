package com.companyname.absence_management.services;

import com.companyname.absence_management.config.AIConfig;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class GeminiAPIServiceTest {
    
    private MockWebServer mockWebServer;
    private GeminiAPIService geminiAPIService;
    private AIConfig aiConfig;
    private ObjectMapper objectMapper;
    
    @BeforeEach
    void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();
        
        // Setup AI config
        aiConfig = new AIConfig();
        AIConfig.Gemini geminiConfig = new AIConfig.Gemini();
        geminiConfig.setApiKey("test-api-key");
        geminiConfig.setApiUrl(mockWebServer.url("/").toString().replaceAll("/$", ""));
        geminiConfig.setTimeoutSeconds(30);
        aiConfig.setGemini(geminiConfig);
        
        objectMapper = new ObjectMapper();
        geminiAPIService = new GeminiAPIService(aiConfig, objectMapper);
    }
    
    @AfterEach
    void tearDown() throws IOException {
        mockWebServer.shutdown();
    }
    
    @Test
    void testCallGeminiAPI_TextResponse() throws Exception {
        // Mock response for text response
        String mockResponse = """
            {
              "candidates": [
                {
                  "content": {
                    "parts": [
                      {
                        "text": "Hello! I'm Alex, your friendly absence management assistant. How can I help you today?"
                      }
                    ]
                  }
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        List<String> conversationHistory = Arrays.asList("user: Hi", "ai: Hello there!");
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, conversationHistory);
        
        StepVerifier.create(responseMono)
                .assertNext(response -> {
                    assertTrue(response.isTextResponse());
                    assertEquals("Hello! I'm Alex, your friendly absence management assistant. How can I help you today?", response.getText());
                })
                .verifyComplete();
        
        // Verify the request was made correctly
        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("POST", request.getMethod());
        assertTrue(request.getPath().contains("key=test-api-key"));
        assertEquals(MediaType.APPLICATION_JSON_VALUE, request.getHeader(HttpHeaders.CONTENT_TYPE));
        
        // Verify request body structure
        JsonNode requestBody = objectMapper.readTree(request.getBody().readUtf8());
        assertTrue(requestBody.has("contents"));
        assertTrue(requestBody.has("tools"));
        assertTrue(requestBody.has("generationConfig"));
    }
    
    @Test
    void testCallGeminiAPI_MarkAbsenceFunctionCall() throws Exception {
        // Mock response for function call
        String mockResponse = """
            {
              "candidates": [
                {
                  "content": {
                    "parts": [
                      {
                        "functionCall": {
                          "name": "markAbsence",
                          "args": {
                            "employeeName": "John Doe",
                            "dates": ["2025-08-25"],
                            "status": "A"
                          }
                        }
                      }
                    ]
                  }
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Mark John Doe absent today";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .assertNext(response -> {
                    assertTrue(response.isFunctionCall());
                    assertEquals("markAbsence", response.getFunctionName());
                    
                    JsonNode args = response.getFunctionArgs();
                    assertEquals("John Doe", args.get("employeeName").asText());
                    assertEquals("A", args.get("status").asText());
                    assertTrue(args.get("dates").isArray());
                    assertEquals("2025-08-25", args.get("dates").get(0).asText());
                })
                .verifyComplete();
    }
    
    @Test
    void testCallGeminiAPI_QueryAbsenceFunctionCall() throws Exception {
        // Mock response for query function call
        String mockResponse = """
            {
              "candidates": [
                {
                  "content": {
                    "parts": [
                      {
                        "functionCall": {
                          "name": "queryAbsence",
                          "args": {
                            "queryType": "byDate",
                            "dates": ["2025-08-15"],
                            "statusFilter": ["A"]
                          }
                        }
                      }
                    ]
                  }
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Who was absent on August 15th?";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .assertNext(response -> {
                    assertTrue(response.isFunctionCall());
                    assertEquals("queryAbsence", response.getFunctionName());
                    
                    JsonNode args = response.getFunctionArgs();
                    assertEquals("byDate", args.get("queryType").asText());
                    assertTrue(args.get("dates").isArray());
                    assertEquals("2025-08-15", args.get("dates").get(0).asText());
                    assertTrue(args.get("statusFilter").isArray());
                    assertEquals("A", args.get("statusFilter").get(0).asText());
                })
                .verifyComplete();
    }
    
    @Test
    void testCallGeminiAPI_ErrorResponse() throws Exception {
        // Mock error response
        String errorResponse = """
            {
              "error": {
                "code": 400,
                "message": "Invalid API key",
                "status": "INVALID_ARGUMENT"
              }
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(400)
                .setBody(errorResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("Invalid API key") &&
                    ((GeminiAPIService.GeminiAPIException) throwable).getStatusCode() == 400)
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_EmptyResponse() throws Exception {
        // Mock empty response
        String mockResponse = """
            {
              "candidates": []
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof RuntimeException &&
                    (throwable.getMessage().contains("No response candidates from Gemini API") ||
                     throwable.getMessage().contains("Failed to call Gemini API")))
                .verify();
    }
    
    @Test
    void testBuildSystemPrompt() {
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith", "Bob Johnson");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        
        assertNotNull(systemPrompt);
        assertTrue(systemPrompt.contains("Alex"));
        assertTrue(systemPrompt.contains("John Doe, Jane Smith, Bob Johnson"));
        assertTrue(systemPrompt.contains("markAbsence"));
        assertTrue(systemPrompt.contains("queryAbsence"));
        assertTrue(systemPrompt.contains("P = Present"));
        assertTrue(systemPrompt.contains("A = Absent"));
        assertTrue(systemPrompt.contains("V = Vacation"));
    }
    
    @Test
    void testGeminiResponse_TextResponse() {
        GeminiAPIService.GeminiResponse response = new GeminiAPIService.GeminiResponse(
                GeminiAPIService.GeminiResponse.ResponseType.TEXT, 
                "Hello there!", 
                null, 
                null
        );
        
        assertTrue(response.isTextResponse());
        assertFalse(response.isFunctionCall());
        assertEquals("Hello there!", response.getText());
        assertNull(response.getFunctionName());
        assertNull(response.getFunctionArgs());
    }
    
    @Test
    void testGeminiResponse_FunctionCall() throws Exception {
        JsonNode args = objectMapper.readTree("""
            {
              "employeeName": "John Doe",
              "dates": ["2025-08-25"],
              "status": "A"
            }
            """);
        
        GeminiAPIService.GeminiResponse response = new GeminiAPIService.GeminiResponse(
                GeminiAPIService.GeminiResponse.ResponseType.FUNCTION_CALL, 
                null, 
                "markAbsence", 
                args
        );
        
        assertFalse(response.isTextResponse());
        assertTrue(response.isFunctionCall());
        assertNull(response.getText());
        assertEquals("markAbsence", response.getFunctionName());
        assertEquals("John Doe", response.getFunctionArgs().get("employeeName").asText());
    }
    
    // Additional comprehensive test cases for edge cases and error handling
    
    @Test
    void testCallGeminiAPI_NullSystemPrompt_ThrowsException() {
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(null, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof IllegalArgumentException &&
                    throwable.getMessage().contains("System prompt cannot be null or empty"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_EmptySystemPrompt_ThrowsException() {
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI("", userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof IllegalArgumentException &&
                    throwable.getMessage().contains("System prompt cannot be null or empty"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_NullUserInput_ThrowsException() {
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, null, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof IllegalArgumentException &&
                    throwable.getMessage().contains("User input cannot be null or empty"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_EmptyUserInput_ThrowsException() {
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, "", null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof IllegalArgumentException &&
                    throwable.getMessage().contains("User input cannot be null or empty"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_MissingApiKey_ThrowsException() throws IOException {
        // Setup AI config with missing API key
        AIConfig testConfig = new AIConfig();
        AIConfig.Gemini geminiConfig = new AIConfig.Gemini();
        geminiConfig.setApiKey(null);
        geminiConfig.setApiUrl(mockWebServer.url("/").toString().replaceAll("/$", ""));
        geminiConfig.setTimeoutSeconds(30);
        testConfig.setGemini(geminiConfig);
        
        GeminiAPIService testService = new GeminiAPIService(testConfig, objectMapper);
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = testService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = testService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("Gemini API key is not configured"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_MissingApiUrl_ThrowsException() throws IOException {
        // Setup AI config with missing API URL
        AIConfig testConfig = new AIConfig();
        AIConfig.Gemini geminiConfig = new AIConfig.Gemini();
        geminiConfig.setApiKey("test-key");
        geminiConfig.setApiUrl(null);
        geminiConfig.setTimeoutSeconds(30);
        testConfig.setGemini(geminiConfig);
        
        GeminiAPIService testService = new GeminiAPIService(testConfig, objectMapper);
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = testService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = testService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("Gemini API URL is not configured"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_NetworkTimeout_ThrowsException() throws Exception {
        // Setup a slow response that will timeout
        mockWebServer.enqueue(new MockResponse()
                .setBodyDelay(35, java.util.concurrent.TimeUnit.SECONDS) // Longer than timeout
                .setBody("{}"));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    (throwable.getMessage().contains("timed out") || 
                     throwable.getMessage().contains("timeout")))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_UnauthorizedError_ThrowsException() throws Exception {
        String errorResponse = """
            {
              "error": {
                "code": 401,
                "message": "Request had invalid authentication credentials",
                "status": "UNAUTHENTICATED"
              }
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(401)
                .setBody(errorResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("Authentication failed") &&
                    ((GeminiAPIService.GeminiAPIException) throwable).getStatusCode() == 401)
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_RateLimitError_ThrowsException() throws Exception {
        String errorResponse = """
            {
              "error": {
                "code": 429,
                "message": "Quota exceeded",
                "status": "RESOURCE_EXHAUSTED"
              }
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(429)
                .setBody(errorResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("Rate limit exceeded") &&
                    ((GeminiAPIService.GeminiAPIException) throwable).getStatusCode() == 429)
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_ServerError_ThrowsException() throws Exception {
        String errorResponse = """
            {
              "error": {
                "code": 500,
                "message": "Internal server error",
                "status": "INTERNAL"
              }
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(500)
                .setBody(errorResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("server error") &&
                    ((GeminiAPIService.GeminiAPIException) throwable).getStatusCode() == 500)
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_InvalidJsonResponse_ThrowsException() throws Exception {
        // Mock invalid JSON response
        String invalidJson = "{ invalid json }";
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(invalidJson)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("Invalid JSON response"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_SafetyFilteredResponse_ThrowsException() throws Exception {
        // Mock response that was blocked by safety filters
        String mockResponse = """
            {
              "candidates": [
                {
                  "finishReason": "SAFETY",
                  "safetyRatings": [
                    {
                      "category": "HARM_CATEGORY_HARASSMENT",
                      "probability": "HIGH"
                    }
                  ]
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("blocked by safety filters"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_RecitationFilteredResponse_ThrowsException() throws Exception {
        // Mock response that was blocked due to recitation
        String mockResponse = """
            {
              "candidates": [
                {
                  "finishReason": "RECITATION",
                  "content": {
                    "parts": []
                  }
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("blocked due to recitation"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_MissingContentInCandidate_ThrowsException() throws Exception {
        // Mock response with candidate but no content
        String mockResponse = """
            {
              "candidates": [
                {
                  "finishReason": "STOP"
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("missing content"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_MissingPartsInContent_ThrowsException() throws Exception {
        // Mock response with content but no parts
        String mockResponse = """
            {
              "candidates": [
                {
                  "content": {
                    "role": "model"
                  }
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("missing parts"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_EmptyPartsArray_ThrowsException() throws Exception {
        // Mock response with empty parts array
        String mockResponse = """
            {
              "candidates": [
                {
                  "content": {
                    "parts": []
                  }
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Hello";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("No valid response content found"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_FunctionCallMissingName_ThrowsException() throws Exception {
        // Mock response with function call but missing name
        String mockResponse = """
            {
              "candidates": [
                {
                  "content": {
                    "parts": [
                      {
                        "functionCall": {
                          "args": {
                            "employeeName": "John Doe"
                          }
                        }
                      }
                    ]
                  }
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Mark John absent today";
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, null);
        
        StepVerifier.create(responseMono)
                .expectErrorMatches(throwable -> 
                    throwable instanceof GeminiAPIService.GeminiAPIException &&
                    throwable.getMessage().contains("missing name"))
                .verify();
    }
    
    @Test
    void testCallGeminiAPI_WithConversationHistory() throws Exception {
        // Mock response for text response
        String mockResponse = """
            {
              "candidates": [
                {
                  "content": {
                    "parts": [
                      {
                        "text": "Based on our previous conversation, I understand you want to continue."
                      }
                    ]
                  }
                }
              ]
            }
            """;
        
        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .addHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE));
        
        List<String> employeeNames = Arrays.asList("John Doe", "Jane Smith");
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        String userInput = "Continue with that";
        List<String> conversationHistory = Arrays.asList(
            "user: Mark John absent today",
            "assistant: I've marked John as absent for today."
        );
        
        Mono<GeminiAPIService.GeminiResponse> responseMono = geminiAPIService.callGeminiAPI(systemPrompt, userInput, conversationHistory);
        
        StepVerifier.create(responseMono)
                .assertNext(response -> {
                    assertTrue(response.isTextResponse());
                    assertTrue(response.getText().contains("previous conversation"));
                })
                .verifyComplete();
        
        // Verify the request included conversation history
        RecordedRequest request = mockWebServer.takeRequest();
        String requestBody = request.getBody().readUtf8();
        assertTrue(requestBody.contains("Recent conversation"));
        assertTrue(requestBody.contains("Mark John absent today"));
        assertTrue(requestBody.contains("I've marked John as absent"));
    }
    
    @Test
    void testBuildSystemPrompt_EmptyEmployeeList() {
        List<String> employeeNames = Arrays.asList();
        String systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames);
        
        assertNotNull(systemPrompt);
        assertTrue(systemPrompt.contains("Alex"));
        assertTrue(systemPrompt.contains("markAbsence"));
        assertTrue(systemPrompt.contains("queryAbsence"));
        // Should handle empty employee list gracefully
        assertTrue(systemPrompt.contains("AVAILABLE EMPLOYEES: "));
    }
    
    @Test
    void testBuildSystemPrompt_NullEmployeeList() {
        assertThrows(NullPointerException.class, () -> {
            geminiAPIService.buildSystemPrompt(null);
        });
    }
    
    @Test
    void testGeminiAPIException_WithStatusCode() {
        GeminiAPIService.GeminiAPIException exception = new GeminiAPIService.GeminiAPIException("Test error", 400);
        
        assertEquals("Test error", exception.getMessage());
        assertEquals(400, exception.getStatusCode());
    }
    
    @Test
    void testGeminiAPIException_DefaultStatusCode() {
        GeminiAPIService.GeminiAPIException exception = new GeminiAPIService.GeminiAPIException("Test error", 500);
        
        assertEquals("Test error", exception.getMessage());
        assertEquals(500, exception.getStatusCode());
    }}
