package com.companyname.absence_management.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "ai")
public class AIConfig {
    
    private Gemini gemini = new Gemini();
    private Conversation conversation = new Conversation();
    
    public Gemini getGemini() {
        return gemini;
    }
    
    public void setGemini(Gemini gemini) {
        this.gemini = gemini;
    }
    
    public Conversation getConversation() {
        return conversation;
    }
    
    public void setConversation(Conversation conversation) {
        this.conversation = conversation;
    }
    
    public static class Gemini {
        private String apiKey;
        private String apiUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent";
        private int timeoutSeconds = 30;
        
        public String getApiKey() {
            return apiKey;
        }
        
        public void setApiKey(String apiKey) {
            this.apiKey = apiKey;
        }
        
        public String getApiUrl() {
            return apiUrl;
        }
        
        public void setApiUrl(String apiUrl) {
            this.apiUrl = apiUrl;
        }
        
        public int getTimeoutSeconds() {
            return timeoutSeconds;
        }
        
        public void setTimeoutSeconds(int timeoutSeconds) {
            this.timeoutSeconds = timeoutSeconds;
        }
    }
    
    public static class Conversation {
        private int timeoutMinutes = 30;
        private int maxConversationHistory = 10;
        
        public int getTimeoutMinutes() {
            return timeoutMinutes;
        }
        
        public void setTimeoutMinutes(int timeoutMinutes) {
            this.timeoutMinutes = timeoutMinutes;
        }
        
        public int getMaxConversationHistory() {
            return maxConversationHistory;
        }
        
        public void setMaxConversationHistory(int maxConversationHistory) {
            this.maxConversationHistory = maxConversationHistory;
        }
    }
}