package com.companyname.absence_management.controllers;

import com.companyname.absence_management.dto.ChatRequestDTO;
import com.companyname.absence_management.dto.ChatResponseDTO;
import com.companyname.absence_management.services.AIService;
import com.companyname.absence_management.services.AbsenceService;
import com.companyname.absence_management.services.EmployeeService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

class AIControllerTest {

    @Mock
    private AbsenceService absenceService;

    @Mock
    private EmployeeService employeeService;

    @Mock
    private AIService aiService;

    @InjectMocks
    private AIController aiController;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testChatEndpoint_ValidRequest_ReturnsSuccess() {
        // Arrange
        ChatRequestDTO request = new ChatRequestDTO("Hello", "test-conversation-id");
        ChatResponseDTO expectedResponse = new ChatResponseDTO(true, "Hello! How can I help you?", "test-conversation-id");
        
        when(aiService.processChatMessage(anyString(), anyString()))
                .thenReturn(Mono.just(expectedResponse));

        // Act
        Mono<ResponseEntity<ChatResponseDTO>> result = aiController.chat(request);

        // Assert
        StepVerifier.create(result)
                .assertNext(responseEntity -> {
                    assertEquals(HttpStatus.OK, responseEntity.getStatusCode());
                    assertNotNull(responseEntity.getBody());
                    assertTrue(responseEntity.getBody().isSuccess());
                    assertEquals("Hello! How can I help you?", responseEntity.getBody().getResponse());
                    assertEquals("test-conversation-id", responseEntity.getBody().getConversationId());
                })
                .verifyComplete();
    }

    @Test
    void testChatEndpoint_EmptyMessage_ReturnsBadRequest() {
        // Arrange
        ChatRequestDTO request = new ChatRequestDTO("", "test-conversation-id");

        // Act
        Mono<ResponseEntity<ChatResponseDTO>> result = aiController.chat(request);

        // Assert
        StepVerifier.create(result)
                .assertNext(responseEntity -> {
                    assertEquals(HttpStatus.BAD_REQUEST, responseEntity.getStatusCode());
                    assertNotNull(responseEntity.getBody());
                    assertFalse(responseEntity.getBody().isSuccess());
                    assertTrue(responseEntity.getBody().getError().contains("didn't receive any message"));
                })
                .verifyComplete();
    }

    @Test
    void testChatEndpoint_NullMessage_ReturnsBadRequest() {
        // Arrange
        ChatRequestDTO request = new ChatRequestDTO(null, "test-conversation-id");

        // Act
        Mono<ResponseEntity<ChatResponseDTO>> result = aiController.chat(request);

        // Assert
        StepVerifier.create(result)
                .assertNext(responseEntity -> {
                    assertEquals(HttpStatus.BAD_REQUEST, responseEntity.getStatusCode());
                    assertNotNull(responseEntity.getBody());
                    assertFalse(responseEntity.getBody().isSuccess());
                    assertTrue(responseEntity.getBody().getError().contains("didn't receive any message"));
                })
                .verifyComplete();
    }

    @Test
    void testChatEndpoint_NoConversationId_GeneratesNewId() {
        // Arrange
        ChatRequestDTO request = new ChatRequestDTO("Hello", null);
        ChatResponseDTO expectedResponse = new ChatResponseDTO(true, "Hello! How can I help you?", null);
        
        when(aiService.processChatMessage(anyString(), anyString()))
                .thenReturn(Mono.just(expectedResponse));

        // Act
        Mono<ResponseEntity<ChatResponseDTO>> result = aiController.chat(request);

        // Assert
        StepVerifier.create(result)
                .assertNext(responseEntity -> {
                    assertEquals(HttpStatus.OK, responseEntity.getStatusCode());
                    assertNotNull(responseEntity.getBody());
                    assertTrue(responseEntity.getBody().isSuccess());
                    assertNotNull(responseEntity.getBody().getConversationId());
                    assertFalse(responseEntity.getBody().getConversationId().isEmpty());
                })
                .verifyComplete();
    }

    @Test
    void testChatEndpoint_AIServiceError_ReturnsInternalServerError() {
        // Arrange
        ChatRequestDTO request = new ChatRequestDTO("Hello", "test-conversation-id");
        
        when(aiService.processChatMessage(anyString(), anyString()))
                .thenReturn(Mono.error(new RuntimeException("AI service error")));

        // Act
        Mono<ResponseEntity<ChatResponseDTO>> result = aiController.chat(request);

        // Assert
        StepVerifier.create(result)
                .assertNext(responseEntity -> {
                    assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, responseEntity.getStatusCode());
                    assertNotNull(responseEntity.getBody());
                    assertFalse(responseEntity.getBody().isSuccess());
                    assertTrue(responseEntity.getBody().getError().contains("unexpected problem") || 
                              responseEntity.getBody().getError().contains("try again"));
                    assertEquals("test-conversation-id", responseEntity.getBody().getConversationId());
                })
                .verifyComplete();
    }
}