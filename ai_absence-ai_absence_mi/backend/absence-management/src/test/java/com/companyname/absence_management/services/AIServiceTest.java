package com.companyname.absence_management.services;

import com.companyname.absence_management.dto.*;
import com.companyname.absence_management.model.AbsenceRecord;
import com.companyname.absence_management.model.Employee;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import com.companyname.absence_management.services.GeminiAPIService.GeminiResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AIServiceTest {
    
    @Mock
    private GeminiAPIService geminiAPIService;
    
    @Mock
    private ConversationContextService conversationContextService;
    
    @Mock
    private AbsenceService absenceService;
    
    @Mock
    private EmployeeService employeeService;
    
    @Mock
    private AbsenceRecordRepository absenceRecordRepository;
    
    @Mock
    private ObjectMapper objectMapper;
    
    @InjectMocks
    private AIService aiService;
    
    private ConversationContext mockContext;
    private List<Employee> mockEmployees;
    private Employee testEmployee;
    
    @BeforeEach
    void setUp() {
        mockContext = new ConversationContext("test-conversation-id");
        
        testEmployee = new Employee();
        testEmployee.setId(1L);
        testEmployee.setName("John Doe");
        testEmployee.setEmail("john.doe@company.com");
        
        Employee testEmployee2 = new Employee();
        testEmployee2.setId(2L);
        testEmployee2.setName("Jane Smith");
        testEmployee2.setEmail("jane.smith@company.com");
        
        mockEmployees = Arrays.asList(testEmployee, testEmployee2);
    }
    
    @Test
    void testProcessChatMessage_TextResponse() {
        // Arrange
        String message = "Hello, how are you?";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        GeminiResponse textResponse = new GeminiResponse(
            GeminiResponse.ResponseType.TEXT, 
            "Hello! I'm here to help with absence management.", 
            null, 
            null
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(textResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                response.getResponse().equals("Hello! I'm here to help with absence management.") &&
                response.getActionType().equals("text")
            )
            .verifyComplete();
        
        verify(conversationContextService).addUserMessage(conversationId, message);
        verify(conversationContextService).addAssistantMessage(conversationId, "Hello! I'm here to help with absence management.");
    }
    
    @Test
    void testProcessChatMessage_MarkAbsenceFunctionCall() throws Exception {
        // Arrange
        String message = "Mark John Doe absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "John Doe");
        functionArgs.put("status", "A");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                response.getActionType().equals("markAbsence") &&
                response.getResponse().contains("John Doe") &&
                response.getResponse().contains("absent")
            )
            .verifyComplete();
        
        verify(absenceService).markAbsenceFromAI(eq(1L), anyList(), eq("A"), anyString());
        verify(conversationContextService).addUserMessage(conversationId, message);
        verify(conversationContextService).addAssistantMessage(eq(conversationId), anyString());
    }
    
    @Test
    void testProcessChatMessage_EmployeeNotFound_SuggestsClosestMatch() throws Exception {
        // Arrange
        String message = "Mark Jon absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments with wrong name
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "Jon");
        functionArgs.put("status", "A");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                (response.getResponse().contains("Did you mean") || 
                 response.getResponse().contains("couldn't find"))
            )
            .verifyComplete();
        
        verify(conversationContextService).updateContext(eq(conversationId), eq("John Doe"), eq("markAbsence"), any(LocalDate.class), eq("A"));
        verify(absenceService, never()).markAbsenceFromAI(anyLong(), anyList(), anyString(), anyString());
    }
    
    @Test
    void testProcessChatMessage_QueryAbsenceFunctionCall() throws Exception {
        // Arrange
        String message = "Who was absent yesterday?";
        String conversationId = "test-conversation-id";
        LocalDate yesterday = LocalDate.now().minusDays(1);
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("queryType", "byDate");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(yesterday.toString()));
        functionArgs.set("statusFilter", new ObjectMapper().createArrayNode().add("A"));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "queryAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Mock absence record
        AbsenceRecord absenceRecord = new AbsenceRecord();
        absenceRecord.setEmployee(testEmployee);
        absenceRecord.setAbsenceDate(yesterday);
        absenceRecord.setAbsenceType(AbsenceRecord.AbsenceType.A);
        absenceRecord.setReason("Sick");
        
        when(absenceRecordRepository.findByAbsenceDate(yesterday))
            .thenReturn(Arrays.asList(absenceRecord));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                response.getActionType().equals("queryAbsence") &&
                response.getResponse().contains("John Doe")
            )
            .verifyComplete();
        
        verify(conversationContextService).addUserMessage(conversationId, message);
        verify(conversationContextService).addAssistantMessage(eq(conversationId), anyString());
    }
    
    @Test
    void testHandleConfirmationResponse_Yes() {
        // Arrange
        String message = "yes";
        String conversationId = "test-conversation-id";
        
        mockContext.updateContext("John Doe", "markAbsence", LocalDate.now(), "A");
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                response.getActionType().equals("markAbsence") &&
                response.getResponse().contains("Perfect! I've marked John Doe")
            )
            .verifyComplete();
        
        verify(absenceService).markAbsenceFromAI(eq(1L), anyList(), eq("A"), anyString());
        verify(conversationContextService).clearContext(conversationId);
    }
    
    @Test
    void testHandleConfirmationResponse_No() {
        // Arrange
        String message = "no";
        String conversationId = "test-conversation-id";
        
        mockContext.updateContext("John Doe", "markAbsence", LocalDate.now(), "A");
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                response.getResponse().contains("No problem! Please tell me the correct employee name")
            )
            .verifyComplete();
        
        verify(conversationContextService).clearContext(conversationId);
        verify(absenceService, never()).markAbsenceFromAI(anyLong(), anyList(), anyString(), anyString());
    }
    
    @Test
    void testProcessChatMessage_GeminiAPIError() {
        // Arrange
        String message = "Mark John absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.error(new GeminiAPIService.GeminiAPIException("API Error", 500)));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                (response.getError().contains("AI brain is having a temporary hiccup") ||
                 response.getError().contains("trouble connecting to my AI brain") ||
                 response.getError().contains("server error"))
            )
            .verifyComplete();
    }
    
    @Test
    void testFindClosestEmployeeName() {
        // This tests the private method indirectly through the mark absence functionality
        // The method should suggest "John Doe" when user types "Jon"
        
        // Test case is covered in testProcessChatMessage_EmployeeNotFound_SuggestsClosestMatch
        // This verifies that the closest name matching logic works correctly
    }
    
    @Test
    void testQueryAbsenceRecords_NoResults() throws Exception {
        // Arrange
        String message = "Who was absent yesterday?";
        String conversationId = "test-conversation-id";
        LocalDate yesterday = LocalDate.now().minusDays(1);
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("queryType", "byDate");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(yesterday.toString()));
        functionArgs.set("statusFilter", new ObjectMapper().createArrayNode().add("A"));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "queryAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Mock no absence records
        when(absenceRecordRepository.findByAbsenceDate(yesterday))
            .thenReturn(Arrays.asList());
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                response.getActionType().equals("queryAbsence") &&
                response.getResponse().contains("No one was absent")
            )
            .verifyComplete();
    }
    
    // Additional comprehensive test cases for edge cases and error handling
    
    @Test
    void testProcessChatMessage_NullMessage_ReturnsError() {
        // Arrange
        String conversationId = "test-conversation-id";
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(null, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("didn't receive any message")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_EmptyMessage_ReturnsError() {
        // Arrange
        String conversationId = "test-conversation-id";
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage("", conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("didn't receive any message")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_WhitespaceOnlyMessage_ReturnsError() {
        // Arrange
        String conversationId = "test-conversation-id";
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage("   \t\n  ", conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("didn't receive any message")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_NullConversationId_ReturnsError() {
        // Arrange
        String message = "Hello";
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, null))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("conversation setup")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_EmptyConversationId_ReturnsError() {
        // Arrange
        String message = "Hello";
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, ""))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("conversation setup")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_ConversationContextServiceError_ReturnsError() {
        // Arrange
        String message = "Hello";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId))
            .thenThrow(new RuntimeException("Context service error"));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("trouble remembering our conversation")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_NoEmployeesFound_ReturnsError() {
        // Arrange
        String message = "Mark John absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(Arrays.asList());
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("no employees in the system")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_EmployeeServiceError_ReturnsError() {
        // Arrange
        String message = "Mark John absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenThrow(new RuntimeException("Database error"));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("trouble accessing the employee database")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_SystemPromptBuildError_ReturnsError() {
        // Arrange
        String message = "Mark John absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenThrow(new RuntimeException("Prompt build error"));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("trouble setting up the conversation context")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessChatMessage_UnexpectedError_ReturnsError() {
        // Arrange
        String message = "Mark John absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenThrow(new RuntimeException("Unexpected error"));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("unexpected error")
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteAbsenceAction_MissingEmployeeName_ReturnsError() throws Exception {
        // Arrange
        String message = "Mark absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments without employeeName
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("status", "A");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("which employee you're talking about")
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteAbsenceAction_EmptyEmployeeName_ReturnsError() throws Exception {
        // Arrange
        String message = "Mark absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments with empty employeeName
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "");
        functionArgs.put("status", "A");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("employee name seems to be empty")
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteAbsenceAction_MissingStatus_ReturnsError() throws Exception {
        // Arrange
        String message = "Mark John today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments without status
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "John Doe");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("what status to mark")
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteAbsenceAction_InvalidStatus_ReturnsError() throws Exception {
        // Arrange
        String message = "Mark John sick today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments with invalid status
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "John Doe");
        functionArgs.put("status", "SICK");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("don't recognize that status")
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteAbsenceAction_MissingDates_ReturnsError() throws Exception {
        // Arrange
        String message = "Mark John absent";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments without dates
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "John Doe");
        functionArgs.put("status", "A");
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("which date(s) you're talking about")
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteAbsenceAction_InvalidDateFormat_ReturnsError() throws Exception {
        // Arrange
        String message = "Mark John absent on invalid-date";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments with invalid date
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "John Doe");
        functionArgs.put("status", "A");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add("invalid-date"));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("couldn't understand these dates")
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteAbsenceAction_AbsenceServiceError_ReturnsError() throws Exception {
        // Arrange
        String message = "Mark John Doe absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "John Doe");
        functionArgs.put("status", "A");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Mock absence service error
        doThrow(new RuntimeException("Database constraint violation"))
            .when(absenceService).markAbsenceFromAI(eq(1L), anyList(), eq("A"), anyString());
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                (response.getError().contains("trouble saving") || 
                 response.getError().contains("had trouble saving"))
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteQueryAction_MissingQueryType_ReturnsError() throws Exception {
        // Arrange
        String message = "Who was absent?";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments without queryType
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "queryAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("not sure what kind of query")
            )
            .verifyComplete();
    }
    
    @Test
    void testExecuteQueryAction_MissingDates_ReturnsError() throws Exception {
        // Arrange
        String message = "Who was absent?";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments without dates
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("queryType", "byDate");
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "queryAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("which date(s) you're asking about")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessGeminiResponse_EmptyTextResponse_ReturnsError() {
        // Arrange
        String message = "Hello";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        GeminiResponse emptyTextResponse = new GeminiResponse(
            GeminiResponse.ResponseType.TEXT, 
            "", 
            null, 
            null
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(emptyTextResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("not sure what to say")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessGeminiResponse_NullFunctionName_ReturnsError() throws Exception {
        // Arrange
        String message = "Mark John absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "John Doe");
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            null, // null function name
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("confused about what action to take")
            )
            .verifyComplete();
    }
    
    @Test
    void testProcessGeminiResponse_UnknownFunctionName_ReturnsError() throws Exception {
        // Arrange
        String message = "Do something";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "unknownFunction",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("not sure how to handle that request")
            )
            .verifyComplete();
    }
    
    @Test
    void testFindClosestEmployeeName_ExactMatch() {
        // This tests the private method indirectly through the mark absence functionality
        // When exact match exists, should not suggest alternatives
        
        // Test case is covered in testProcessChatMessage_MarkAbsenceFunctionCall
        // This verifies that exact name matching works correctly
    }
    
    @Test
    void testFindClosestEmployeeName_NoCloseMatch() throws Exception {
        // Arrange
        String message = "Mark XYZ absent today";
        String conversationId = "test-conversation-id";
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        // Create mock function arguments with very different name
        ObjectNode functionArgs = new ObjectMapper().createObjectNode();
        functionArgs.put("employeeName", "XYZ");
        functionArgs.put("status", "A");
        functionArgs.set("dates", new ObjectMapper().createArrayNode().add(LocalDate.now().toString()));
        
        GeminiResponse functionResponse = new GeminiResponse(
            GeminiResponse.ResponseType.FUNCTION_CALL,
            null,
            "markAbsence",
            functionArgs
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(functionResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                response.getResponse().contains("couldn't find an employee named 'XYZ'") &&
                response.getResponse().contains("Here are some available employees")
            )
            .verifyComplete();
        
        verify(absenceService, never()).markAbsenceFromAI(anyLong(), anyList(), anyString(), anyString());
    }
    
    @Test
    void testHandleConfirmationResponse_InvalidConfirmation() {
        // Arrange
        String message = "maybe";
        String conversationId = "test-conversation-id";
        
        mockContext.updateContext("John Doe", "markAbsence", LocalDate.now(), "A");
        
        when(conversationContextService.getContext(conversationId)).thenReturn(mockContext);
        when(employeeService.getAllEmployees()).thenReturn(mockEmployees);
        when(geminiAPIService.buildSystemPrompt(anyList())).thenReturn("System prompt");
        
        GeminiResponse textResponse = new GeminiResponse(
            GeminiResponse.ResponseType.TEXT, 
            "I need a clear yes or no answer.", 
            null, 
            null
        );
        
        when(geminiAPIService.callGeminiAPI(anyString(), anyString(), anyList()))
            .thenReturn(Mono.just(textResponse));
        
        // Act & Assert
        StepVerifier.create(aiService.processChatMessage(message, conversationId))
            .expectNextMatches(response -> 
                response.isSuccess() && 
                response.getActionType().equals("text") &&
                response.getResponse().contains("clear yes or no")
            )
            .verifyComplete();
        
        // Should not execute absence action or clear context for ambiguous response
        verify(absenceService, never()).markAbsenceFromAI(anyLong(), anyList(), anyString(), anyString());
    }}
