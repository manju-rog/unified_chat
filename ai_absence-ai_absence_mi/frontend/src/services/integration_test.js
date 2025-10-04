/**
 * Frontend Integration Tests for AI Chatbot
 * Tests the complete flow from frontend to backend
 */

const API_BASE_URL = 'http://localhost:8080/api/ai';

class IntegrationTester {
  constructor() {
    this.conversationId = this.generateConversationId();
    this.testResults = [];
  }

  generateConversationId() {
    return 'test_conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  async callBackendAI(message) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        conversationId: this.conversationId
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.response || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  logResult(testName, success, message, response = null) {
    const result = {
      test: testName,
      success,
      message,
      response,
      timestamp: new Date().toISOString()
    };
    this.testResults.push(result);
    
    const status = success ? '✅ PASS' : '❌ FAIL';
    console.log(`${status} ${testName}: ${message}`);
    if (response) {
      console.log('Response:', response);
    }
  }

  async testBasicConnection() {
    try {
      const response = await this.callBackendAI("Hello");
      
      if (response.success) {
        this.logResult('Basic Connection', true, 'Successfully connected to backend AI API', response);
        return true;
      } else {
        this.logResult('Basic Connection', false, 'Backend returned error: ' + response.error, response);
        return false;
      }
    } catch (error) {
      this.logResult('Basic Connection', false, 'Failed to connect: ' + error.message);
      return false;
    }
  }

  async testMarkAbsence() {
    try {
      const response = await this.callBackendAI("Mark Manju absent today");
      
      if (response.success && response.actionType === 'markAbsence') {
        this.logResult('Mark Absence', true, 'Successfully marked absence', response);
        return true;
      } else {
        this.logResult('Mark Absence', false, 'Unexpected response format', response);
        return false;
      }
    } catch (error) {
      this.logResult('Mark Absence', false, 'Error: ' + error.message);
      return false;
    }
  }

  async testQueryAbsence() {
    try {
      const response = await this.callBackendAI("Who was absent yesterday?");
      
      if (response.success && response.actionType === 'queryAbsence') {
        this.logResult('Query Absence', true, 'Successfully queried absences', response);
        return true;
      } else {
        this.logResult('Query Absence', false, 'Unexpected response format', response);
        return false;
      }
    } catch (error) {
      this.logResult('Query Absence', false, 'Error: ' + error.message);
      return false;
    }
  }

  async testConversationContext() {
    try {
      // First message with typo
      const response1 = await this.callBackendAI("Mark Manu absent today");
      
      if (!response1.success) {
        this.logResult('Conversation Context', false, 'First message failed', response1);
        return false;
      }

      // Should suggest "Manju"
      if (!response1.response.toLowerCase().includes('manju') && 
          !response1.response.toLowerCase().includes('did you mean')) {
        this.logResult('Conversation Context', false, 'No name suggestion provided', response1);
        return false;
      }

      // Confirm with "yes"
      const response2 = await this.callBackendAI("yes");
      
      if (response2.success && response2.actionType === 'markAbsence') {
        this.logResult('Conversation Context', true, 'Successfully handled confirmation flow', {
          suggestion: response1,
          confirmation: response2
        });
        return true;
      } else {
        this.logResult('Conversation Context', false, 'Confirmation failed', response2);
        return false;
      }
    } catch (error) {
      this.logResult('Conversation Context', false, 'Error: ' + error.message);
      return false;
    }
  }

  async testErrorHandling() {
    try {
      const response = await this.callBackendAI("Mark NonExistentEmployee absent today");
      
      if (response.success) {
        // Should handle gracefully, either with suggestion or error message
        this.logResult('Error Handling', true, 'Gracefully handled invalid employee', response);
        return true;
      } else {
        // Error response is also acceptable
        this.logResult('Error Handling', true, 'Returned appropriate error', response);
        return true;
      }
    } catch (error) {
      this.logResult('Error Handling', false, 'Unexpected error: ' + error.message);
      return false;
    }
  }

  async testNonAbsenceQuery() {
    try {
      const response = await this.callBackendAI("What's the weather like?");
      
      if (response.success && response.actionType === 'text') {
        // Should redirect to absence-related topics
        if (response.response.toLowerCase().includes('absence') || 
            response.response.toLowerCase().includes('help')) {
          this.logResult('Non-Absence Query', true, 'Properly redirected to absence topics', response);
          return true;
        } else {
          this.logResult('Non-Absence Query', false, 'Did not redirect to absence topics', response);
          return false;
        }
      } else {
        this.logResult('Non-Absence Query', false, 'Unexpected response format', response);
        return false;
      }
    } catch (error) {
      this.logResult('Non-Absence Query', false, 'Error: ' + error.message);
      return false;
    }
  }

  async testVacationMarking() {
    try {
      const response = await this.callBackendAI("Put Ganesh on vacation tomorrow");
      
      if (response.success && response.actionType === 'markAbsence') {
        const actionData = response.actionData;
        if (actionData && actionData.status === 'V') {
          this.logResult('Vacation Marking', true, 'Successfully marked vacation', response);
          return true;
        } else {
          this.logResult('Vacation Marking', false, 'Wrong status type', response);
          return false;
        }
      } else {
        this.logResult('Vacation Marking', false, 'Unexpected response format', response);
        return false;
      }
    } catch (error) {
      this.logResult('Vacation Marking', false, 'Error: ' + error.message);
      return false;
    }
  }

  async runAllTests() {
    console.log('🚀 Starting Frontend-Backend Integration Tests...\n');
    
    const tests = [
      { name: 'Basic Connection', fn: () => this.testBasicConnection() },
      { name: 'Mark Absence', fn: () => this.testMarkAbsence() },
      { name: 'Query Absence', fn: () => this.testQueryAbsence() },
      { name: 'Conversation Context', fn: () => this.testConversationContext() },
      { name: 'Error Handling', fn: () => this.testErrorHandling() },
      { name: 'Non-Absence Query', fn: () => this.testNonAbsenceQuery() },
      { name: 'Vacation Marking', fn: () => this.testVacationMarking() }
    ];

    let passedTests = 0;
    let totalTests = tests.length;

    for (const test of tests) {
      try {
        console.log(`\n🧪 Running ${test.name}...`);
        const result = await test.fn();
        if (result) passedTests++;
        
        // Small delay between tests
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (error) {
        this.logResult(test.name, false, 'Test execution failed: ' + error.message);
      }
    }

    console.log('\n📊 Test Results Summary:');
    console.log(`Total Tests: ${totalTests}`);
    console.log(`Passed: ${passedTests}`);
    console.log(`Failed: ${totalTests - passedTests}`);
    console.log(`Success Rate: ${((passedTests / totalTests) * 100).toFixed(1)}%`);

    if (passedTests === totalTests) {
      console.log('\n🎉 All tests passed! Frontend-Backend integration is working correctly.');
    } else {
      console.log('\n⚠️  Some tests failed. Please check the logs above for details.');
    }

    return {
      total: totalTests,
      passed: passedTests,
      failed: totalTests - passedTests,
      successRate: (passedTests / totalTests) * 100,
      results: this.testResults
    };
  }

  // Method to test specific functionality manually
  async testSpecificScenario(message) {
    try {
      console.log(`\n🧪 Testing: "${message}"`);
      const response = await this.callBackendAI(message);
      console.log('Response:', response);
      return response;
    } catch (error) {
      console.error('Error:', error.message);
      return null;
    }
  }
}

// Export for use in browser console or Node.js
if (typeof window !== 'undefined') {
  // Browser environment
  window.IntegrationTester = IntegrationTester;
  
  // Auto-run tests if requested
  if (window.location.search.includes('runTests=true')) {
    const tester = new IntegrationTester();
    tester.runAllTests();
  }
} else {
  // Node.js environment
  module.exports = IntegrationTester;
}

// Usage examples:
// const tester = new IntegrationTester();
// tester.runAllTests();
// tester.testSpecificScenario("Mark John absent today");