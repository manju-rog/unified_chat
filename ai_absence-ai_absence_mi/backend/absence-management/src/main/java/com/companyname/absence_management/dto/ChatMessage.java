package com.companyname.absence_management.dto;

import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessage {
    
    private String role; // "user" or "assistant"
    private String content;
    private LocalDateTime timestamp;
    private String messageType; // "text", "function_call", "function_response"
    
    // Convenience constructors
    public ChatMessage(String role, String content) {
        this.role = role;
        this.content = content;
        this.timestamp = LocalDateTime.now();
        this.messageType = "text";
    }
    
    public ChatMessage(String role, String content, String messageType) {
        this.role = role;
        this.content = content;
        this.timestamp = LocalDateTime.now();
        this.messageType = messageType;
    }
    
    public static ChatMessage userMessage(String content) {
        return new ChatMessage("user", content);
    }
    
    public static ChatMessage assistantMessage(String content) {
        return new ChatMessage("assistant", content);
    }
}