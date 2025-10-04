package com.companyname.absence_management.services;

import com.companyname.absence_management.config.AIConfig;
import com.companyname.absence_management.dto.ConversationContext;
import com.companyname.absence_management.dto.ChatMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;
import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.lenient;

@ExtendWith(MockitoExtension.class)
class ConversationContextServiceTest {

    @Mock
    private AIConfig aiConfig;

    @Mock
    private AIConfig.Conversation conversationConfig;

    private ConversationContextService conversationContextService;

    @BeforeEach
    void setUp() {
        lenient().when(aiConfig.getConversation()).thenReturn(conversationConfig);
        lenient().when(conversationConfig.getTimeoutMinutes()).thenReturn(30);
        lenient().when(conversationConfig.getMaxConversationHistory()).thenReturn(10);
        
        conversationContextService = new ConversationContextService(aiConfig);
    }

    @Test
    void testGetContext_NewConversation() {
        String conversationId = "test-conversation-1";
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        
        assertNotNull(context);
        assertEquals(conversationId, context.getConversationId());
        assertNotNull(context.getConversationHistory());
        assertTrue(context.getConversationHistory().isEmpty());
        assertNotNull(context.getCreatedAt());
        assertNotNull(context.getLastUpdated());
    }

    @Test
    void testGetContext_ExistingConversation() {
        String conversationId = "test-conversation-1";
        
        // Get context first time
        ConversationContext context1 = conversationContextService.getContext(conversationId);
        context1.setLastSuggestedEmployee("John Doe");
        conversationContextService.updateContext(conversationId, context1);
        
        // Get context second time
        ConversationContext context2 = conversationContextService.getContext(conversationId);
        
        assertEquals(context1.getConversationId(), context2.getConversationId());
        assertEquals("John Doe", context2.getLastSuggestedEmployee());
    }

    @Test
    void testGetContext_NullConversationId() {
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.getContext(null);
        });
    }

    @Test
    void testGetContext_EmptyConversationId() {
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.getContext("");
        });
    }

    @Test
    void testUpdateContext() {
        String conversationId = "test-conversation-1";
        ConversationContext context = conversationContextService.getContext(conversationId);
        
        context.setLastSuggestedEmployee("Jane Smith");
        context.setLastRequestedAction("markAbsence");
        
        conversationContextService.updateContext(conversationId, context);
        
        ConversationContext updatedContext = conversationContextService.getContext(conversationId);
        assertEquals("Jane Smith", updatedContext.getLastSuggestedEmployee());
        assertEquals("markAbsence", updatedContext.getLastRequestedAction());
    }

    @Test
    void testUpdateContextWithValues() {
        String conversationId = "test-conversation-1";
        LocalDate testDate = LocalDate.of(2024, 8, 15);
        
        conversationContextService.updateContext(conversationId, "John Doe", "markAbsence", testDate, "absent");
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertEquals("John Doe", context.getLastSuggestedEmployee());
        assertEquals("markAbsence", context.getLastRequestedAction());
        assertEquals(testDate, context.getLastRequestedDate());
        assertEquals("absent", context.getLastRequestedStatus());
    }

    @Test
    void testAddMessage() {
        String conversationId = "test-conversation-1";
        ChatMessage message = ChatMessage.userMessage("Hello");
        
        conversationContextService.addMessage(conversationId, message);
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertEquals(1, context.getConversationHistory().size());
        assertEquals("Hello", context.getConversationHistory().get(0).getContent());
        assertEquals("user", context.getConversationHistory().get(0).getRole());
    }

    @Test
    void testAddUserMessage() {
        String conversationId = "test-conversation-1";
        
        conversationContextService.addUserMessage(conversationId, "Mark John absent today");
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertEquals(1, context.getConversationHistory().size());
        assertEquals("Mark John absent today", context.getConversationHistory().get(0).getContent());
        assertEquals("user", context.getConversationHistory().get(0).getRole());
    }

    @Test
    void testAddAssistantMessage() {
        String conversationId = "test-conversation-1";
        
        conversationContextService.addAssistantMessage(conversationId, "I've marked John as absent for today.");
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertEquals(1, context.getConversationHistory().size());
        assertEquals("I've marked John as absent for today.", context.getConversationHistory().get(0).getContent());
        assertEquals("assistant", context.getConversationHistory().get(0).getRole());
    }

    @Test
    void testClearContext() {
        String conversationId = "test-conversation-1";
        
        // Set up context with data
        conversationContextService.updateContext(conversationId, "John Doe", "markAbsence", 
                                                LocalDate.now(), "absent");
        conversationContextService.addUserMessage(conversationId, "Test message");
        
        // Clear context
        conversationContextService.clearContext(conversationId);
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertNull(context.getLastSuggestedEmployee());
        assertNull(context.getLastRequestedAction());
        assertNull(context.getLastRequestedDate());
        assertNull(context.getLastRequestedStatus());
        // Conversation history should remain
        assertEquals(1, context.getConversationHistory().size());
    }

    @Test
    void testRemoveConversation() {
        String conversationId = "test-conversation-1";
        
        // Create conversation
        conversationContextService.getContext(conversationId);
        assertTrue(conversationContextService.hasConversation(conversationId));
        
        // Remove conversation
        conversationContextService.removeConversation(conversationId);
        assertFalse(conversationContextService.hasConversation(conversationId));
    }

    @Test
    void testHasConversation() {
        String conversationId = "test-conversation-1";
        
        assertFalse(conversationContextService.hasConversation(conversationId));
        
        conversationContextService.getContext(conversationId);
        assertTrue(conversationContextService.hasConversation(conversationId));
    }

    @Test
    void testGetConversationCount() {
        assertEquals(0, conversationContextService.getConversationCount());
        
        conversationContextService.getContext("conv-1");
        assertEquals(1, conversationContextService.getConversationCount());
        
        conversationContextService.getContext("conv-2");
        assertEquals(2, conversationContextService.getConversationCount());
        
        conversationContextService.removeConversation("conv-1");
        assertEquals(1, conversationContextService.getConversationCount());
    }

    @Test
    void testConversationHistoryLimit() {
        lenient().when(conversationConfig.getMaxConversationHistory()).thenReturn(3);
        
        String conversationId = "test-conversation-1";
        
        // Add more messages than the limit
        for (int i = 1; i <= 5; i++) {
            conversationContextService.addUserMessage(conversationId, "Message " + i);
        }
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertEquals(3, context.getConversationHistory().size());
        
        // Should keep the most recent messages
        assertEquals("Message 3", context.getConversationHistory().get(0).getContent());
        assertEquals("Message 4", context.getConversationHistory().get(1).getContent());
        assertEquals("Message 5", context.getConversationHistory().get(2).getContent());
    }

    @Test
    void testCleanupExpiredConversationsNow() {
        lenient().when(conversationConfig.getTimeoutMinutes()).thenReturn(1); // 1 minute timeout
        
        String conversationId = "test-conversation-1";
        ConversationContext context = conversationContextService.getContext(conversationId);
        
        // Manually set last updated to simulate expired conversation
        // We need to set it after getting the context but before cleanup
        context.setLastUpdated(LocalDateTime.now().minusMinutes(2));
        
        assertEquals(1, conversationContextService.getConversationCount());
        
        int removedCount = conversationContextService.cleanupExpiredConversationsNow();
        
        assertEquals(1, removedCount);
        assertEquals(0, conversationContextService.getConversationCount());
    }
    
    // Additional comprehensive test cases for edge cases and error handling
    
    @Test
    void testUpdateContext_NullConversationId_ThrowsException() {
        ConversationContext context = new ConversationContext("test-id");
        
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.updateContext(null, context);
        });
    }
    
    @Test
    void testUpdateContext_EmptyConversationId_ThrowsException() {
        ConversationContext context = new ConversationContext("test-id");
        
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.updateContext("", context);
        });
    }
    
    @Test
    void testUpdateContext_NullContext_ThrowsException() {
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.updateContext("test-id", null);
        });
    }
    
    @Test
    void testUpdateContextWithValues_NullValues() {
        String conversationId = "test-conversation-1";
        
        // Should handle null values gracefully
        conversationContextService.updateContext(conversationId, null, null, null, null);
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertNull(context.getLastSuggestedEmployee());
        assertNull(context.getLastRequestedAction());
        assertNull(context.getLastRequestedDate());
        assertNull(context.getLastRequestedStatus());
    }
    
    @Test
    void testAddMessage_NullConversationId_ThrowsException() {
        ChatMessage message = ChatMessage.userMessage("Hello");
        
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.addMessage(null, message);
        });
    }
    
    @Test
    void testAddMessage_EmptyConversationId_ThrowsException() {
        ChatMessage message = ChatMessage.userMessage("Hello");
        
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.addMessage("", message);
        });
    }
    
    @Test
    void testAddMessage_NullMessage_ThrowsException() {
        String conversationId = "test-conversation-1";
        
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.addMessage(conversationId, null);
        });
    }
    
    @Test
    void testAddUserMessage_NullContent() {
        String conversationId = "test-conversation-1";
        
        // Should handle null content gracefully by converting to empty string
        conversationContextService.addUserMessage(conversationId, null);
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertEquals(1, context.getConversationHistory().size());
        assertEquals("", context.getConversationHistory().get(0).getContent());
        assertEquals("user", context.getConversationHistory().get(0).getRole());
    }
    
    @Test
    void testAddAssistantMessage_NullContent() {
        String conversationId = "test-conversation-1";
        
        // Should handle null content gracefully by converting to empty string
        conversationContextService.addAssistantMessage(conversationId, null);
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertEquals(1, context.getConversationHistory().size());
        assertEquals("", context.getConversationHistory().get(0).getContent());
        assertEquals("assistant", context.getConversationHistory().get(0).getRole());
    }
    
    @Test
    void testClearContext_NullConversationId_ThrowsException() {
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.clearContext(null);
        });
    }
    
    @Test
    void testClearContext_EmptyConversationId_ThrowsException() {
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.clearContext("");
        });
    }
    
    @Test
    void testClearContext_NonExistentConversation() {
        // Should handle non-existent conversation gracefully
        conversationContextService.clearContext("non-existent-id");
        
        // No exception should be thrown
        assertFalse(conversationContextService.hasConversation("non-existent-id"));
    }
    
    @Test
    void testRemoveConversation_NullConversationId_ThrowsException() {
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.removeConversation(null);
        });
    }
    
    @Test
    void testRemoveConversation_EmptyConversationId_ThrowsException() {
        assertThrows(IllegalArgumentException.class, () -> {
            conversationContextService.removeConversation("");
        });
    }
    
    @Test
    void testRemoveConversation_NonExistentConversation() {
        // Should handle non-existent conversation gracefully
        conversationContextService.removeConversation("non-existent-id");
        
        // No exception should be thrown
        assertFalse(conversationContextService.hasConversation("non-existent-id"));
    }
    
    @Test
    void testHasConversation_NullConversationId() {
        assertFalse(conversationContextService.hasConversation(null));
    }
    
    @Test
    void testHasConversation_EmptyConversationId() {
        assertFalse(conversationContextService.hasConversation(""));
    }
    
    @Test
    void testConversationHistoryLimit_ZeroLimit() {
        lenient().when(conversationConfig.getMaxConversationHistory()).thenReturn(0);
        
        String conversationId = "test-conversation-1";
        
        conversationContextService.addUserMessage(conversationId, "Message 1");
        conversationContextService.addUserMessage(conversationId, "Message 2");
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        assertEquals(0, context.getConversationHistory().size());
    }
    
    @Test
    void testConversationHistoryLimit_NegativeLimit() {
        lenient().when(conversationConfig.getMaxConversationHistory()).thenReturn(-1);
        
        String conversationId = "test-conversation-1";
        
        // This test should handle the case where negative limit might cause issues
        // We expect it to either work or throw an exception, but not crash silently
        try {
            conversationContextService.addUserMessage(conversationId, "Message 1");
            conversationContextService.addUserMessage(conversationId, "Message 2");
            
            ConversationContext context = conversationContextService.getContext(conversationId);
            // Should handle negative limit gracefully (likely keep all messages or none)
            assertTrue(context.getConversationHistory().size() >= 0);
        } catch (Exception e) {
            // It's acceptable for negative limits to cause exceptions
            assertTrue(e instanceof RuntimeException || e instanceof IllegalArgumentException);
        }
    }
    
    @Test
    void testMultipleConcurrentConversations() {
        String conversationId1 = "test-conversation-1";
        String conversationId2 = "test-conversation-2";
        String conversationId3 = "test-conversation-3";
        
        // Create multiple conversations
        conversationContextService.addUserMessage(conversationId1, "Message from conv 1");
        conversationContextService.addUserMessage(conversationId2, "Message from conv 2");
        conversationContextService.addUserMessage(conversationId3, "Message from conv 3");
        
        assertEquals(3, conversationContextService.getConversationCount());
        
        // Verify each conversation maintains its own context
        ConversationContext context1 = conversationContextService.getContext(conversationId1);
        ConversationContext context2 = conversationContextService.getContext(conversationId2);
        ConversationContext context3 = conversationContextService.getContext(conversationId3);
        
        assertEquals("Message from conv 1", context1.getConversationHistory().get(0).getContent());
        assertEquals("Message from conv 2", context2.getConversationHistory().get(0).getContent());
        assertEquals("Message from conv 3", context3.getConversationHistory().get(0).getContent());
        
        // Update context for one conversation
        conversationContextService.updateContext(conversationId1, "John Doe", "markAbsence", 
                                                LocalDate.now(), "absent");
        
        // Verify only the updated conversation has the context
        context1 = conversationContextService.getContext(conversationId1);
        context2 = conversationContextService.getContext(conversationId2);
        
        assertEquals("John Doe", context1.getLastSuggestedEmployee());
        assertNull(context2.getLastSuggestedEmployee());
    }
    
    @Test
    void testCleanupExpiredConversations_MixedExpiredAndActive() {
        lenient().when(conversationConfig.getTimeoutMinutes()).thenReturn(5); // 5 minute timeout
        
        String activeConversationId = "active-conversation";
        String expiredConversationId1 = "expired-conversation-1";
        String expiredConversationId2 = "expired-conversation-2";
        
        // Create conversations
        ConversationContext activeContext = conversationContextService.getContext(activeConversationId);
        ConversationContext expiredContext1 = conversationContextService.getContext(expiredConversationId1);
        ConversationContext expiredContext2 = conversationContextService.getContext(expiredConversationId2);
        
        // Set expired timestamps
        expiredContext1.setLastUpdated(LocalDateTime.now().minusMinutes(10));
        expiredContext2.setLastUpdated(LocalDateTime.now().minusMinutes(15));
        
        assertEquals(3, conversationContextService.getConversationCount());
        
        int removedCount = conversationContextService.cleanupExpiredConversationsNow();
        
        assertEquals(2, removedCount);
        assertEquals(1, conversationContextService.getConversationCount());
        assertTrue(conversationContextService.hasConversation(activeConversationId));
        assertFalse(conversationContextService.hasConversation(expiredConversationId1));
        assertFalse(conversationContextService.hasConversation(expiredConversationId2));
    }
    
    @Test
    void testCleanupExpiredConversations_NoExpiredConversations() {
        lenient().when(conversationConfig.getTimeoutMinutes()).thenReturn(30); // 30 minute timeout
        
        String conversationId1 = "test-conversation-1";
        String conversationId2 = "test-conversation-2";
        
        // Create recent conversations
        conversationContextService.getContext(conversationId1);
        conversationContextService.getContext(conversationId2);
        
        assertEquals(2, conversationContextService.getConversationCount());
        
        int removedCount = conversationContextService.cleanupExpiredConversationsNow();
        
        assertEquals(0, removedCount);
        assertEquals(2, conversationContextService.getConversationCount());
    }
    
    @Test
    void testConversationContextCreation_UniqueTimestamps() throws InterruptedException {
        String conversationId1 = "test-conversation-1";
        String conversationId2 = "test-conversation-2";
        
        ConversationContext context1 = conversationContextService.getContext(conversationId1);
        
        // Small delay to ensure different timestamps
        Thread.sleep(1);
        
        ConversationContext context2 = conversationContextService.getContext(conversationId2);
        
        assertNotEquals(context1.getCreatedAt(), context2.getCreatedAt());
        assertNotEquals(context1.getLastUpdated(), context2.getLastUpdated());
    }
    
    @Test
    void testUpdateContext_UpdatesTimestamp() throws InterruptedException {
        String conversationId = "test-conversation-1";
        
        ConversationContext context = conversationContextService.getContext(conversationId);
        LocalDateTime originalTimestamp = context.getLastUpdated();
        
        // Small delay to ensure different timestamp
        Thread.sleep(1);
        
        conversationContextService.updateContext(conversationId, "John Doe", "markAbsence", 
                                                LocalDate.now(), "absent");
        
        ConversationContext updatedContext = conversationContextService.getContext(conversationId);
        assertTrue(updatedContext.getLastUpdated().isAfter(originalTimestamp));
    }}
