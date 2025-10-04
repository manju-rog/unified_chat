// AI Integration Test Suite - DEPRECATED
// This test suite was for the old direct Gemini API integration
// The AI functionality has been moved to the backend
// TODO: Update this to test the new backend API integration

/**
 * DEPRECATED: Test suite for old direct Gemini API integration
 * The AI functionality has been moved to the backend
 * This file is kept for reference but should be updated to test the new backend API
 */
export class AIIntegrationTest {
  constructor() {
    this.testEmployees = [
      { id: 1, name: "John Doe" },
      { id: 2, name: "Jane Smith" },
      { id: 3, name: "Bob Johnson" },
      { id: 4, name: "Alice Brown" },
      { id: 5, name: "Charlie Wilson" }
    ];
  }

  async runAllTests() {
    console.log('🚀 Starting AI Integration Tests...\n');

    const tests = [
      this.testGeminiConnection,
      this.testBasicAbsenceMarking,
      this.testMultipleDates,
      this.testEmployeeNameMatching,
      this.testConversationContext,
      this.testNonAbsenceQueries,
      this.testInvalidRequests,
      this.testDateParsing
    ];

    let passed = 0;
    let failed = 0;

    for (const test of tests) {
      try {
        await test.call(this);
        console.log(`✅ ${test.name} - PASSED\n`);
        passed++;
      } catch (error) {
        console.error(`❌ ${test.name} - FAILED:`, error.message, '\n');
        failed++;
      }
    }

    console.log(`\n📊 Test Results: ${passed} passed, ${failed} failed`);
    return { passed, failed };
  }

  async testGeminiConnection() {
    console.log('Testing Gemini API connection...');
    const isConnected = await testGeminiConnection();
    if (!isConnected) {
      throw new Error('Failed to connect to Gemini API');
    }
    console.log('Gemini API connection successful');
  }

  async testBasicAbsenceMarking() {
    console.log('Testing basic absence marking...');

    const testCases = [
      {
        input: "Mark John Doe absent today",
        expectedAction: "markAbsence",
        expectedStatus: "A"
      },
      {
        input: "Set Jane Smith as present tomorrow",
        expectedAction: "markAbsence",
        expectedStatus: "P"
      },
      {
        input: "Mark Bob Johnson on vacation for December 25th",
        expectedAction: "markAbsence",
        expectedStatus: "V"
      }
    ];

    for (const testCase of testCases) {
      const result = await getAiAction(testCase.input, this.testEmployees, []);

      if (result.action !== testCase.expectedAction) {
        throw new Error(`Expected action ${testCase.expectedAction}, got ${result.action}`);
      }

      if (result.args && result.args.status !== testCase.expectedStatus) {
        throw new Error(`Expected status ${testCase.expectedStatus}, got ${result.args.status}`);
      }

      console.log(`✓ "${testCase.input}" -> ${result.action} (${result.args?.status})`);
    }
  }

  async testMultipleDates() {
    console.log('Testing multiple date handling...');

    const result = await getAiAction(
      "Mark Alice Brown absent from December 23rd to December 25th",
      this.testEmployees,
      []
    );

    if (result.action !== 'markAbsence') {
      throw new Error(`Expected markAbsence action, got ${result.action}`);
    }

    if (!result.args.dates || result.args.dates.length === 0) {
      throw new Error('Expected multiple dates in result');
    }

    console.log(`✓ Multiple dates handled: ${result.args.dates.length} dates`);
  }

  async testEmployeeNameMatching() {
    console.log('Testing employee name matching...');

    const testCases = [
      { input: "Mark john absent today", expectedName: "John Doe" },
      { input: "Set jane as present", expectedName: "Jane Smith" },
      { input: "Mark charlie on vacation", expectedName: "Charlie Wilson" }
    ];

    for (const testCase of testCases) {
      const result = await getAiAction(testCase.input, this.testEmployees, []);

      if (result.action === 'markAbsence') {
        if (result.args.employeeName !== testCase.expectedName) {
          throw new Error(`Expected ${testCase.expectedName}, got ${result.args.employeeName}`);
        }
        console.log(`✓ "${testCase.input}" -> ${result.args.employeeName}`);
      } else if (result.text && result.text.includes(testCase.expectedName)) {
        console.log(`✓ "${testCase.input}" -> Suggested correct name`);
      } else {
        throw new Error(`Failed to match or suggest correct name for: ${testCase.input}`);
      }
    }
  }

  async testConversationContext() {
    console.log('Testing conversation context and confirmations...');

    // Test wrong name suggestion and confirmation
    const wrongNameResult = await getAiAction("mark john absent today", this.testEmployees, []);

    if (!wrongNameResult.text || !wrongNameResult.text.includes('Did you mean')) {
      throw new Error('Expected name suggestion for unknown employee');
    }

    console.log(`✓ Wrong name handling: ${wrongNameResult.text.substring(0, 50)}...`);

    // Test confirmation
    const confirmationResult = await getAiAction("yes", this.testEmployees, [
      { type: 'user', content: 'mark john absent today' },
      { type: 'ai', content: wrongNameResult.text }
    ]);

    if (confirmationResult.action !== 'markAbsence') {
      throw new Error('Expected confirmation to trigger markAbsence action');
    }

    console.log(`✓ Confirmation handling: ${confirmationResult.args.employeeName} marked as ${confirmationResult.args.status}`);
  }

  async testNonAbsenceQueries() {
    console.log('Testing non-absence query handling...');

    const nonAbsenceQueries = [
      "What's the weather like?",
      "Tell me a joke",
      "How are you?",
      "What can you do?"
    ];

    for (const query of nonAbsenceQueries) {
      const result = await getAiAction(query, this.testEmployees, []);

      if (result.action === 'markAbsence') {
        throw new Error(`Non-absence query "${query}" should not trigger markAbsence`);
      }

      if (!result.text) {
        throw new Error(`Expected text response for non-absence query: ${query}`);
      }

      // Check if response mentions absence management
      const mentionsAbsence = result.text.toLowerCase().includes('absence') ||
        result.text.toLowerCase().includes('absent') ||
        result.text.toLowerCase().includes('attendance');

      if (!mentionsAbsence) {
        console.log(`⚠️  Response might not redirect to absence management: "${result.text.substring(0, 50)}..."`);
      }

      console.log(`✓ "${query}" -> Handled appropriately`);
    }
  }

  async testInvalidRequests() {
    console.log('Testing invalid request handling...');

    const invalidInputs = [
      "Hello, how are you?",
      "What's the weather like?",
      "Mark unknown_employee absent",
      "Delete all records"
    ];

    for (const input of invalidInputs) {
      const result = await getAiAction(input, this.testEmployees, []);

      if (result.action === 'markAbsence') {
        throw new Error(`Invalid input "${input}" should not trigger markAbsence`);
      }

      if (!result.text) {
        throw new Error(`Expected text response for invalid input: ${input}`);
      }

      console.log(`✓ "${input}" -> Handled as text response`);
    }
  }

  async testDateParsing() {
    console.log('Testing date parsing capabilities...');

    const dateInputs = [
      "Mark John absent today",
      "Set Jane present tomorrow",
      "Mark Bob on vacation next Monday",
      "Alice absent on December 25th"
    ];

    for (const input of dateInputs) {
      const result = await getAiAction(input, this.testEmployees, []);

      if (result.action === 'markAbsence') {
        if (!result.args.dates || result.args.dates.length === 0) {
          throw new Error(`No dates parsed for: ${input}`);
        }

        // Validate date format (YYYY-MM-DD)
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        for (const date of result.args.dates) {
          if (!dateRegex.test(date)) {
            throw new Error(`Invalid date format: ${date}`);
          }
        }

        console.log(`✓ "${input}" -> ${result.args.dates.join(', ')}`);
      } else {
        console.log(`✓ "${input}" -> Handled as clarification`);
      }
    }
  }

  // Utility method to run a single test
  async runSingleTest(testName) {
    console.log(`🧪 Running single test: ${testName}\n`);

    const testMethod = this[testName];
    if (!testMethod) {
      throw new Error(`Test method ${testName} not found`);
    }

    try {
      await testMethod.call(this);
      console.log(`✅ ${testName} - PASSED`);
      return true;
    } catch (error) {
      console.error(`❌ ${testName} - FAILED:`, error.message);
      return false;
    }
  }
}

// Export for easy testing in browser console
window.AIIntegrationTest = AIIntegrationTest;

// Auto-run tests if in development mode
if (process.env.NODE_ENV === 'development') {
  console.log('AI Integration Test Suite loaded. Run new AIIntegrationTest().runAllTests() to test.');
}