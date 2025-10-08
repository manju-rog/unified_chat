package com.companyname.absence_management.services;

import com.companyname.absence_management.config.AIConfig;
import com.companyname.absence_management.dto.ConversationContext;
import com.companyname.absence_management.dto.ChatMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;
import java.util.Optional;

@Service
public class ConversationContextService {
    
    private static final Logger logger = LoggerFactory.getLogger(ConversationContextService.class);
    
    private final Map<String, ConversationContext> conversationStore = new ConcurrentHashMap<>();
    private final AIConfig aiConfig;
    
    @Autowired
    public ConversationContextService(AIConfig aiConfig) {
        this.aiConfig = aiConfig;
    }
    
    public ConversationContext getContext(String conversationId) {
        if (conversationId == null || conversationId.trim().isEmpty()) {
            throw new IllegalArgumentException("Conversation ID cannot be null or empty");
        }
        
        try {
            return conversationStore.computeIfAbsent(conversationId, id -> {
                try {
                    return new ConversationContext(id);
                } catch (Exception e) {
                    logger.error("Failed to create new conversation context for ID {}: {}", id, e.getMessage());
                    throw new RuntimeException("Failed to create conversation context", e);
                }
            });
        } catch (Exception e) {
            logger.error("Error getting conversation context for ID {}: {}", conversationId, e.getMessage());
            throw new RuntimeException("Failed to get conversation context", e);
        }
    }
    
    public void updateContext(String conversationId, ConversationContext context) {
        if (conversationId == null || conversationId.trim().isEmpty()) {
            throw new IllegalArgumentException("Conversation ID cannot be null or empty");
        }
        
        if (context == null) {
            throw new IllegalArgumentException("Conversation context cannot be null");
        }
        
        context.setConversationId(conversationId);
        context.setLastUpdated(LocalDateTime.now());
        limitConversationHistory(context);
        conversationStore.put(conversationId, context);
    }
    
    public void updateContext(String conversationId, String suggestedEmployee, 
                            String requestedAction, LocalDate requestedDate, String requestedStatus) {
        ConversationContext context = getContext(conversationId);
        context.updateContext(suggestedEmployee, requestedAction, requestedDate, requestedStatus);
        updateContext(conversationId, context);
    }
    
    public void addMessage(String conversationId, ChatMessage message) {
        if (conversationId == null || conversationId.trim().isEmpty()) {
            throw new IllegalArgumentException("Conversation ID cannot be null or empty");
        }
        
        if (message == null) {
            throw new IllegalArgumentException("Message cannot be null");
        }
        
        try {
            ConversationContext context = getContext(conversationId);
            context.addMessage(message);
            updateContext(conversationId, context);
        } catch (Exception e) {
            logger.error("Failed to add message to conversation {}: {}", conversationId, e.getMessage());
            throw new RuntimeException("Failed to add message to conversation", e);
        }
    }
    
    public void addUserMessage(String conversationId, String content) {
        if (content == null) {
            content = "";
        }
        
        try {
            addMessage(conversationId, ChatMessage.userMessage(content));
        } catch (Exception e) {
            logger.error("Failed to add user message to conversation {}: {}", conversationId, e.getMessage());
            throw new RuntimeException("Failed to add user message", e);
        }
    }
    
    public void addAssistantMessage(String conversationId, String content) {
        if (content == null) {
            content = "";
        }
        
        try {
            addMessage(conversationId, ChatMessage.assistantMessage(content));
        } catch (Exception e) {
            logger.error("Failed to add assistant message to conversation {}: {}", conversationId, e.getMessage());
            throw new RuntimeException("Failed to add assistant message", e);
        }
    }
    
    /**
     * Clear conversation context (reset context but keep conversation history)
     */
    public void clearContext(String conversationId) {
        if (conversationId == null || conversationId.trim().isEmpty()) {
            throw new IllegalArgumentException("Conversation ID cannot be null or empty");
        }
        
        ConversationContext context = conversationStore.get(conversationId);
        if (context != null) {
            context.clearContext();
            updateContext(conversationId, context);
            logger.debug("Cleared context for conversation ID: {}", conversationId);
        }
    }
    
    /**
     * Remove conversation entirely
     */
    public void removeConversation(String conversationId) {
        if (conversationId == null || conversationId.trim().isEmpty()) {
            throw new IllegalArgumentException("Conversation ID cannot be null or empty");
        }
        
        conversationStore.remove(conversationId);
        logger.debug("Removed conversation ID: {}", conversationId);
    }
    
    /**
     * Check if conversation exists
     */
    public boolean hasConversation(String conversationId) {
        return conversationId != null && conversationStore.containsKey(conversationId);
    }
    
    /**
     * Get conversation count (for monitoring)
     */
    public int getConversationCount() {
        return conversationStore.size();
    }
    
    /**
     * Limit conversation history to configured maximum
     */
    private void limitConversationHistory(ConversationContext context) {
        if (context.getConversationHistory() != null) {
            int maxHistory = aiConfig.getConversation().getMaxConversationHistory();
            if (context.getConversationHistory().size() > maxHistory) {
                // Keep only the most recent messages
                int startIndex = context.getConversationHistory().size() - maxHistory;
                context.setConversationHistory(
                    context.getConversationHistory().subList(startIndex, context.getConversationHistory().size())
                );
                logger.debug("Limited conversation history to {} messages for conversation: {}", 
                           maxHistory, context.getConversationId());
            }
        }
    }
    
    /**
     * Scheduled cleanup of expired conversations
     * Runs every 5 minutes
     */
    @Scheduled(fixedRate = 300000) // 5 minutes in milliseconds
    public void cleanupExpiredConversations() {
        int timeoutMinutes = aiConfig.getConversation().getTimeoutMinutes();
        int removedCount = 0;
        
        // Create a copy of the keys to avoid ConcurrentModificationException
        for (String conversationId : conversationStore.keySet().toArray(new String[0])) {
            ConversationContext context = conversationStore.get(conversationId);
            if (context != null && context.isExpired(timeoutMinutes)) {
                conversationStore.remove(conversationId);
                removedCount++;
                logger.debug("Removed expired conversation: {}", conversationId);
            }
        }
        
        if (removedCount > 0) {
            logger.info("Cleaned up {} expired conversations. Active conversations: {}", 
                       removedCount, conversationStore.size());
        }
    }
    
    /**
     * Manual cleanup trigger (for testing or administrative purposes)
     */
    public int cleanupExpiredConversationsNow() {
        int timeoutMinutes = aiConfig.getConversation().getTimeoutMinutes();
        int removedCount = 0;
        
        for (String conversationId : conversationStore.keySet().toArray(new String[0])) {
            ConversationContext context = conversationStore.get(conversationId);
            if (context != null && context.isExpired(timeoutMinutes)) {
                conversationStore.remove(conversationId);
                removedCount++;
            }
        }
        
        logger.info("Manual cleanup removed {} expired conversations. Active conversations: {}", 
                   removedCount, conversationStore.size());
        return removedCount;
    }
}