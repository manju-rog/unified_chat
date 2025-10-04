package com.companyname.absence_management.dto;

import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatResponseDTO {
    
    private boolean success;
    private String response;
    private String actionType; // "markAbsence", "queryAbsence", "text"
    private Object actionData; // Action-specific data
    private String error;
    private String conversationId;
    
    // Convenience constructors
    public ChatResponseDTO(boolean success, String response, String conversationId) {
        this.success = success;
        this.response = response;
        this.conversationId = conversationId;
        this.actionType = "text";
    }
    
    public ChatResponseDTO(boolean success, String response, String actionType, Object actionData, String conversationId) {
        this.success = success;
        this.response = response;
        this.actionType = actionType;
        this.actionData = actionData;
        this.conversationId = conversationId;
    }
    
    public static ChatResponseDTO error(String error, String conversationId) {
        ChatResponseDTO response = new ChatResponseDTO();
        response.setSuccess(false);
        response.setError(error);
        response.setConversationId(conversationId);
        return response;
    }
}