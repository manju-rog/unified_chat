package com.companyname.absence_management.dto;

import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ConversationContext {
    
    private String conversationId;
    private String lastSuggestedEmployee;
    private String lastRequestedAction;
    private LocalDate lastRequestedDate;
    private String lastRequestedStatus;
    private List<ChatMessage> conversationHistory;
    private LocalDateTime createdAt;
    private LocalDateTime lastUpdated;
    
    // Constructor with conversation ID
    public ConversationContext(String conversationId) {
        this.conversationId = conversationId;
        this.conversationHistory = new ArrayList<>();
        this.createdAt = LocalDateTime.now();
        this.lastUpdated = LocalDateTime.now();
    }
    
    // Convenience methods
    public void addMessage(ChatMessage message) {
        if (this.conversationHistory == null) {
            this.conversationHistory = new ArrayList<>();
        }
        this.conversationHistory.add(message);
        this.lastUpdated = LocalDateTime.now();
    }
    
    public void addUserMessage(String content) {
        addMessage(ChatMessage.userMessage(content));
    }
    
    public void addAssistantMessage(String content) {
        addMessage(ChatMessage.assistantMessage(content));
    }
    
    public void clearContext() {
        this.lastSuggestedEmployee = null;
        this.lastRequestedAction = null;
        this.lastRequestedDate = null;
        this.lastRequestedStatus = null;
        this.lastUpdated = LocalDateTime.now();
    }
    
    public void updateContext(String suggestedEmployee, String requestedAction, LocalDate requestedDate, String requestedStatus) {
        this.lastSuggestedEmployee = suggestedEmployee;
        this.lastRequestedAction = requestedAction;
        this.lastRequestedDate = requestedDate;
        this.lastRequestedStatus = requestedStatus;
        this.lastUpdated = LocalDateTime.now();
    }
    
    public boolean hasContext() {
        return lastSuggestedEmployee != null || lastRequestedAction != null || 
               lastRequestedDate != null || lastRequestedStatus != null;
    }
    
    public boolean isExpired(int timeoutMinutes) {
        return lastUpdated.isBefore(LocalDateTime.now().minusMinutes(timeoutMinutes));
    }
}