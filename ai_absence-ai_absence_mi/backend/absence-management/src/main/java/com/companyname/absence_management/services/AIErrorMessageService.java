package com.companyname.absence_management.services;

import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.List;
import java.util.Random;

/**
 * Service for generating user-friendly error messages with chatbot personality
 */
@Service
public class AIErrorMessageService {
    
    private final Random random = new Random();
    
    // Fallback messages for when the AI service is completely unavailable
    private final List<String> serviceFallbackMessages = Arrays.asList(
        "I'm having some technical difficulties right now! 🔧 But don't worry - you can still manage attendance manually using the grid above. I'll be back soon!",
        "Oops! My AI brain needs a quick reboot! 🤖 While I'm getting fixed, you can mark attendance directly in the grid. Thanks for your patience!",
        "I seem to be offline at the moment! 📡 No worries though - all the attendance features are still available in the main interface. I'll be back shortly!",
        "Technical timeout on my end! ⏰ You can continue working with the attendance system normally - I'm just the helpful assistant, not the main show!",
        "I'm temporarily out of order! 🚧 But the good news is you can still do everything manually. I'll be back to help soon!"
    );
    
    // Messages for when the user's request can't be processed
    private final List<String> requestFallbackMessages = Arrays.asList(
        "I'm not quite sure what you're asking for! 🤔 I can help you mark employees as Present, Absent, or on Vacation. What would you like to do?",
        "That's a bit confusing for me! 😵‍💫 I'm really good at attendance stuff though - want to mark someone absent or check who was out on a specific day?",
        "I didn't quite catch that! 🎯 I specialize in attendance management. Try asking me to mark someone absent or find out who was off on a particular date!",
        "Hmm, I'm not following! 🤷‍♂️ I'm your attendance assistant - I can mark people present, absent, or on vacation. What do you need help with?",
        "That's outside my expertise! 🎭 I'm all about attendance tracking. Want me to mark someone's status or check absence records?"
    );
    
    // Messages for when employee names aren't found
    private final List<String> employeeNotFoundMessages = Arrays.asList(
        "I couldn't find that employee! 👤 Could you double-check the spelling? Here are some employees I know about: %s",
        "That name doesn't ring a bell! 🔔 Maybe there's a typo? Try one of these: %s",
        "I don't see that employee in my list! 📋 Perhaps you meant one of these: %s",
        "No luck finding that person! 🕵️‍♂️ Here are some similar names: %s",
        "That employee isn't in my database! 💾 Did you mean one of these instead: %s"
    );
    
    // Messages for date parsing issues
    private final List<String> dateFallbackMessages = Arrays.asList(
        "I'm having trouble with that date! 📅 Try something like 'today', 'tomorrow', or 'August 15th'.",
        "That date format is confusing me! 🗓️ Could you try 'today', 'Monday', or 'December 25th'?",
        "I can't quite parse that date! ⏰ How about using 'today', 'next Friday', or 'August 15'?",
        "Date troubles on my end! 📆 Try formats like 'today', 'tomorrow', or 'January 1st'.",
        "I'm struggling with that date format! 🤯 Please try 'today', 'next week', or 'March 15th'."
    );
    
    /**
     * Get a random service fallback message for when AI is completely unavailable
     */
    public String getServiceFallbackMessage() {
        return serviceFallbackMessages.get(random.nextInt(serviceFallbackMessages.size()));
    }
    
    /**
     * Get a random request fallback message for unclear requests
     */
    public String getRequestFallbackMessage() {
        return requestFallbackMessages.get(random.nextInt(requestFallbackMessages.size()));
    }
    
    /**
     * Get a random employee not found message with employee suggestions
     */
    public String getEmployeeNotFoundMessage(String employeeNames) {
        String template = employeeNotFoundMessages.get(random.nextInt(employeeNotFoundMessages.size()));
        return String.format(template, employeeNames);
    }
    
    /**
     * Get a random date parsing fallback message
     */
    public String getDateFallbackMessage() {
        return dateFallbackMessages.get(random.nextInt(dateFallbackMessages.size()));
    }
    
    /**
     * Get a contextual error message based on the error type and context
     */
    public String getContextualErrorMessage(String errorType, String context) {
        switch (errorType.toLowerCase()) {
            case "network":
                return "I can't reach my AI brain right now - network issues! 📡 You can still use the attendance grid manually while I get reconnected!";
            case "timeout":
                return "I'm thinking extra hard about your request but it's taking too long! 🤔 Try a simpler request or use the manual attendance features!";
            case "overload":
                return "I'm getting swamped with requests! 😅 Take a breather and try again in a moment, or use the attendance grid directly!";
            case "parsing":
                return "I got a bit tongue-tied trying to understand that! 😵‍💫 Could you rephrase your request more simply?";
            case "employee":
                return context != null ? getEmployeeNotFoundMessage(context) : "I couldn't find that employee! 👤 Please check the spelling and try again!";
            case "date":
                return getDateFallbackMessage();
            case "service":
                return getServiceFallbackMessage();
            default:
                return getRequestFallbackMessage();
        }
    }
    
    /**
     * Get an encouraging message to help users when things go wrong
     */
    public String getEncouragementMessage() {
        List<String> encouragements = Arrays.asList(
            "Don't worry, these things happen! 😊 I'm here to help once I get my act together!",
            "No stress! 🌟 Technology has its moments. I'll be back to my helpful self soon!",
            "Hey, at least the main attendance system is working perfectly! 💪 I'm just the bonus feature!",
            "Thanks for your patience! 🙏 I promise I'm usually more reliable than this!",
            "Keep calm and carry on! 🎯 I'll sort myself out while you get things done!"
        );
        
        return encouragements.get(random.nextInt(encouragements.size()));
    }
}