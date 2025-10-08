package com.companyname.absence_management.integration;

import com.companyname.absence_management.dto.ChatRequestDTO;
import com.companyname.absence_management.dto.ChatResponseDTO;
import com.companyname.absence_management.model.Employee;
import com.companyname.absence_management.model.AbsenceRecord;
import com.companyname.absence_management.repository.EmployeeRepository;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import com.companyname.absence_management.services.ConversationContextService;
import com.companyname.absence_management.services.EmployeeService;
import com.companyname.absence_management.services.AbsenceService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests specifically focused on testing AI actions with database operations.
 * This test class verifies that the AI can properly query employees from the SQLite database,
 * mark absences that are written to the database, and ensure all CRUD operations work correctly.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("sqlite")
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Transactional
@DisplayName("AI Database Integration Tests")
public class AIDatabaseIntegrationTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private EmployeeRepository employeeRepository;

    @Autowired
    private AbsenceRecordRepository absenceRecordRepository;

    @Autowired
    private ConversationContextService conversationContextService;

    @Autowired
    private EmployeeService employeeService;

    @Autowired
    private AbsenceService absenceService;

    @Autowired
    private ObjectMapper objectMapper;

    private String baseUrl;
    private String conversationId;
    private HttpHeaders headers;

    @BeforeEach
    void setUp() {
        baseUrl = "http://localhost:" + port + "/api/ai";
        conversationId = "db-test-conv-" + UUID.randomUUID().toString();
        
        headers = new HttpHeaders();
        headers.set("Content-Type", "application/json");
        headers.set("Accept", "application/json");

        // Clear any existing conversation context
        conversationContextService.clearContext(conversationId);

        // Set up comprehensive test data
        setupComprehensiveTestData();
    }

    private void setupComprehensiveTestData() {
        // Clear existing data
        absenceRecordRepository.deleteAll();
        employeeRepository.deleteAll();

        // Create diverse set of test employees
        Employee alice = Employee.builder()
                .name("Alice Johnson")
                .email("alice.johnson@company.com")
                .phone("1234567890")
                .department("Engineering")
                .role("Senior Developer")
                .location("New York")
                .employeeId("EMP001")
                .build();
        employeeRepository.save(alice);

        Employee bob = Employee.builder()
                .name("Bob Smith")
                .email("bob.smith@company.com")
                .phone("1234567891")
                .department("Marketing")
                .role("Marketing Manager")
                .location("San Francisco")
                .employeeId("EMP002")
                .build();
        employeeRepository.save(bob);

        Employee charlie = Employee.builder()
                .name("Charlie Brown")
                .email("charlie.brown@company.com")
                .phone("1234567892")
                .department("HR")
                .role("HR Specialist")
                .location("Chicago")
                .employeeId("EMP003")
                .build();
        employeeRepository.save(charlie);

        Employee diana = Employee.builder()
                .name("Diana Prince")
                .email("diana.prince@company.com")
                .phone("1234567893")
                .department("Finance")
                .role("Financial Analyst")
                .location("Boston")
                .employeeId("EMP004")
                .build();
        employeeRepository.save(diana);

        Employee eve = Employee.builder()
                .name("Eve Wilson")
                .email("eve.wilson@company.com")
                .phone("1234567894")
                .department("Engineering")
                .role("DevOps Engineer")
                .location("Seattle")
                .employeeId("EMP005")
                .build();
        employeeRepository.save(eve);

        // Add some historical absence data for testing queries
        LocalDate yesterday = LocalDate.now().minusDays(1);
        LocalDate twoDaysAgo = LocalDate.now().minusDays(2);
        LocalDate lastWeek = LocalDate.now().minusDays(7);

        // Alice was absent yesterday
        AbsenceRecord aliceAbsence = AbsenceRecord.builder()
                .employee(alice)
                .absenceDate(yesterday)
                .absenceType(AbsenceRecord.AbsenceType.A)
                .reason("Sick leave")
                .status(AbsenceRecord.AbsenceStatus.APPROVED)
                .build();
        absenceRecordRepository.save(aliceAbsence);

        // Bob was on vacation two days ago
        AbsenceRecord bobVacation = AbsenceRecord.builder()
                .employee(bob)
                .absenceDate(twoDaysAgo)
                .absenceType(AbsenceRecord.AbsenceType.V)
                .reason("Personal vacation")
                .status(AbsenceRecord.AbsenceStatus.APPROVED)
                .build();
        absenceRecordRepository.save(bobVacation);

        // Charlie was absent last week
        AbsenceRecord charlieAbsence = AbsenceRecord.builder()
                .employee(charlie)
                .absenceDate(lastWeek)
                .absenceType(AbsenceRecord.AbsenceType.A)
                .reason("Medical appointment")
                .status(AbsenceRecord.AbsenceStatus.APPROVED)
                .build();
        absenceRecordRepository.save(charlieAbsence);
    }

    private ResponseEntity<ChatResponseDTO> sendChatMessage(String message) {
        ChatRequestDTO request = new ChatRequestDTO();
        request.setMessage(message);
        request.setConversationId(conversationId);

        HttpEntity<ChatRequestDTO> entity = new HttpEntity<>(request, headers);
        return restTemplate.postForEntity(baseUrl + "/chat", entity, ChatResponseDTO.class);
    }

    @Test
    @DisplayName("AI can query employees from SQLite database")
    void testAICanQueryEmployeesFromDatabase() {
        // Verify employees exist in database first
        List<Employee> allEmployees = employeeService.getAllEmployees();
        assertEquals(5, allEmployees.size(), "Should have 5 test employees in database");

        // Test AI can access employee data through natural language
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Who are all the employees in the system?");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        
        String responseText = response.getBody().getResponse().toLowerCase();
        
        // Verify AI can access and mention employees from database
        assertTrue(responseText.contains("alice") || responseText.contains("employees"), 
                "AI should be able to access employee data from database");
    }

    @Test
    @DisplayName("AI absence marking writes correctly to SQLite database")
    void testAIAbsenceMarkingWritesToDatabase() {
        // Verify no absence exists for Diana today
        Employee diana = employeeRepository.findAll().stream()
                .filter(e -> "Diana Prince".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(diana, "Diana should exist in database");
        
        Optional<AbsenceRecord> beforeAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), LocalDate.now());
        assertFalse(beforeAbsence.isPresent(), "Diana should not have absence record for today initially");

        // Use AI to mark Diana absent today
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Diana Prince absent today");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("markAbsence", response.getBody().getActionType());

        // Verify the absence was written to database
        Optional<AbsenceRecord> afterAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), LocalDate.now());
        assertTrue(afterAbsence.isPresent(), "Absence record should be created in database");
        assertEquals(AbsenceRecord.AbsenceType.A, afterAbsence.get().getAbsenceType());
        assertEquals("Marked by AI Assistant", afterAbsence.get().getReason());
        assertEquals(AbsenceRecord.AbsenceStatus.APPROVED, afterAbsence.get().getStatus());
    }

    @Test
    @DisplayName("AI vacation marking writes correctly to SQLite database")
    void testAIVacationMarkingWritesToDatabase() {
        // Use AI to mark Eve on vacation tomorrow
        LocalDate tomorrow = LocalDate.now().plusDays(1);
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Put Eve Wilson on vacation tomorrow");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("markAbsence", response.getBody().getActionType());

        // Verify vacation was written to database
        Employee eve = employeeRepository.findAll().stream()
                .filter(e -> "Eve Wilson".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(eve);
        
        Optional<AbsenceRecord> vacation = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(eve.getId(), tomorrow);
        assertTrue(vacation.isPresent(), "Vacation record should be created in database");
        assertEquals(AbsenceRecord.AbsenceType.V, vacation.get().getAbsenceType());
        assertEquals("Marked by AI Assistant", vacation.get().getReason());
    }

    @Test
    @DisplayName("AI can query historical absence data from database")
    void testAICanQueryHistoricalAbsenceData() {
        // Test querying who was absent yesterday (Alice should be found)
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Who was absent yesterday?");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("queryAbsence", response.getBody().getActionType());
        
        String responseText = response.getBody().getResponse().toLowerCase();
        assertTrue(responseText.contains("alice"), 
                "AI should find Alice was absent yesterday from database");
    }

    @Test
    @DisplayName("AI can query vacation data from database")
    void testAICanQueryVacationData() {
        // Test querying who was on vacation two days ago (Bob should be found)
        LocalDate twoDaysAgo = LocalDate.now().minusDays(2);
        String query = String.format("Who was on vacation on %s?", twoDaysAgo.toString());
        
        ResponseEntity<ChatResponseDTO> response = sendChatMessage(query);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("queryAbsence", response.getBody().getActionType());
        
        String responseText = response.getBody().getResponse().toLowerCase();
        assertTrue(responseText.contains("bob") || responseText.contains("vacation"), 
                "AI should find Bob was on vacation from database");
    }

    @Test
    @DisplayName("AI handles database updates correctly - marking present removes absence")
    void testAIHandlesDatabaseUpdatesCorrectly() {
        // First mark Charlie absent today
        ResponseEntity<ChatResponseDTO> response1 = sendChatMessage("Mark Charlie Brown absent today");
        assertEquals(HttpStatus.OK, response1.getStatusCode());
        assertTrue(response1.getBody().isSuccess());

        // Verify absence was created
        Employee charlie = employeeRepository.findAll().stream()
                .filter(e -> "Charlie Brown".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(charlie);
        
        Optional<AbsenceRecord> absence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(charlie.getId(), LocalDate.now());
        assertTrue(absence.isPresent(), "Absence should be created");

        // Now mark Charlie present (should remove the absence record)
        ResponseEntity<ChatResponseDTO> response2 = sendChatMessage("Mark Charlie Brown present today");
        assertEquals(HttpStatus.OK, response2.getStatusCode());
        assertTrue(response2.getBody().isSuccess());

        // Verify absence was removed from database
        Optional<AbsenceRecord> afterPresent = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(charlie.getId(), LocalDate.now());
        assertFalse(afterPresent.isPresent(), "Absence record should be removed when marked present");
    }

    @Test
    @DisplayName("AI handles multiple employee database operations")
    void testAIHandlesMultipleEmployeeDatabaseOperations() {
        // Mark multiple employees absent
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Alice Johnson and Bob Smith absent today");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("markAbsence", response.getBody().getActionType());

        // Verify both employees have absence records in database
        Employee alice = employeeRepository.findAll().stream()
                .filter(e -> "Alice Johnson".equals(e.getName()))
                .findFirst().orElse(null);
        Employee bob = employeeRepository.findAll().stream()
                .filter(e -> "Bob Smith".equals(e.getName()))
                .findFirst().orElse(null);
        
        assertNotNull(alice);
        assertNotNull(bob);
        
        Optional<AbsenceRecord> aliceAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(alice.getId(), LocalDate.now());
        Optional<AbsenceRecord> bobAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(bob.getId(), LocalDate.now());
        
        assertTrue(aliceAbsence.isPresent(), "Alice should have absence record");
        assertTrue(bobAbsence.isPresent(), "Bob should have absence record");
        assertEquals(AbsenceRecord.AbsenceType.A, aliceAbsence.get().getAbsenceType());
        assertEquals(AbsenceRecord.AbsenceType.A, bobAbsence.get().getAbsenceType());
    }

    @Test
    @DisplayName("AI handles date range database operations")
    void testAIHandlesDateRangeDatabaseOperations() {
        // Mark Diana absent for a range of dates
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Diana Prince absent from tomorrow to next Wednesday");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("markAbsence", response.getBody().getActionType());

        // Verify multiple absence records were created in database
        Employee diana = employeeRepository.findAll().stream()
                .filter(e -> "Diana Prince".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(diana);
        
        // Check for absence records in the next few days
        LocalDate tomorrow = LocalDate.now().plusDays(1);
        LocalDate dayAfter = LocalDate.now().plusDays(2);
        
        Optional<AbsenceRecord> tomorrowAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), tomorrow);
        Optional<AbsenceRecord> dayAfterAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), dayAfter);
        
        // At least one of these should exist (depending on how the AI interprets the date range)
        assertTrue(tomorrowAbsence.isPresent() || dayAfterAbsence.isPresent(), 
                "At least one absence record should be created for the date range");
    }

    @Test
    @DisplayName("AI database operations maintain data integrity")
    void testAIDatabaseOperationsMaintainDataIntegrity() {
        // Get initial counts
        long initialEmployeeCount = employeeRepository.count();
        long initialAbsenceCount = absenceRecordRepository.count();
        
        assertEquals(5, initialEmployeeCount, "Should start with 5 employees");
        assertEquals(3, initialAbsenceCount, "Should start with 3 historical absence records");

        // Perform multiple AI operations
        sendChatMessage("Mark Alice Johnson absent today");
        sendChatMessage("Put Bob Smith on vacation today");
        sendChatMessage("Mark Charlie Brown present today"); // This should not add a record

        // Verify counts are as expected
        long finalEmployeeCount = employeeRepository.count();
        long finalAbsenceCount = absenceRecordRepository.count();
        
        assertEquals(initialEmployeeCount, finalEmployeeCount, "Employee count should remain unchanged");
        assertEquals(initialAbsenceCount + 2, finalAbsenceCount, "Should have 2 new absence records");

        // Verify data integrity - all absence records should have valid employee references
        List<AbsenceRecord> allAbsences = absenceRecordRepository.findAll();
        for (AbsenceRecord absence : allAbsences) {
            assertNotNull(absence.getEmployee(), "Every absence record should have a valid employee reference");
            assertNotNull(absence.getAbsenceDate(), "Every absence record should have a valid date");
            assertNotNull(absence.getAbsenceType(), "Every absence record should have a valid type");
            assertTrue(employeeRepository.existsById(absence.getEmployee().getId()), 
                    "Employee referenced in absence record should exist in database");
        }
    }

    @Test
    @DisplayName("AI handles database constraint violations gracefully")
    void testAIHandlesDatabaseConstraintViolationsGracefully() {
        // Try to mark a non-existent employee absent
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark NonExistentEmployee absent today");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        
        // Should handle gracefully by suggesting existing employees or asking for clarification
        String responseText = response.getBody().getResponse().toLowerCase();
        assertTrue(responseText.contains("find") || responseText.contains("suggest") || 
                  responseText.contains("available") || responseText.contains("clarify"),
                "AI should handle non-existent employee gracefully");
        
        // Verify no invalid records were created
        List<AbsenceRecord> todayAbsences = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getAbsenceDate().equals(LocalDate.now()))
                .toList();
        
        // All absence records should have valid employee references
        for (AbsenceRecord record : todayAbsences) {
            assertNotNull(record.getEmployee());
            assertTrue(employeeRepository.existsById(record.getEmployee().getId()));
        }
    }

    @Test
    @DisplayName("AI database queries return accurate results")
    void testAIDatabaseQueriesReturnAccurateResults() {
        // Add specific test data
        Employee testEmployee = Employee.builder()
                .name("Test Employee")
                .email("test@company.com")
                .phone("9999999999")
                .department("Testing")
                .role("Test Role")
                .location("Test Location")
                .employeeId("TEST001")
                .build();
        employeeRepository.save(testEmployee);

        LocalDate testDate = LocalDate.now().minusDays(3);
        AbsenceRecord testAbsence = AbsenceRecord.builder()
                .employee(testEmployee)
                .absenceDate(testDate)
                .absenceType(AbsenceRecord.AbsenceType.A)
                .reason("Test absence")
                .status(AbsenceRecord.AbsenceStatus.APPROVED)
                .build();
        absenceRecordRepository.save(testAbsence);

        // Query for this specific absence
        String query = String.format("Who was absent on %s?", testDate.toString());
        ResponseEntity<ChatResponseDTO> response = sendChatMessage(query);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("queryAbsence", response.getBody().getActionType());
        
        // Verify the response includes our test employee
        String responseText = response.getBody().getResponse().toLowerCase();
        assertTrue(responseText.contains("test employee") || responseText.contains("test"),
                "Query should return the test employee who was absent on the specified date");
    }

    @Test
    @DisplayName("AI database operations work with complex employee names")
    void testAIDatabaseOperationsWithComplexEmployeeNames() {
        // Add employee with complex name
        Employee complexNameEmployee = Employee.builder()
                .name("María José García-López")
                .email("maria.garcia@company.com")
                .phone("5555555555")
                .department("International")
                .role("Global Coordinator")
                .location("Madrid")
                .employeeId("INTL001")
                .build();
        employeeRepository.save(complexNameEmployee);

        // Test AI can handle complex names
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark María José García-López absent today");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());

        // Verify the absence was recorded correctly
        Optional<AbsenceRecord> absence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(complexNameEmployee.getId(), LocalDate.now());
        assertTrue(absence.isPresent(), "Should handle complex employee names correctly");
        assertEquals(AbsenceRecord.AbsenceType.A, absence.get().getAbsenceType());
    }

    @Test
    @DisplayName("AI maintains conversation context across database operations")
    void testAIMaintainsConversationContextAcrossDatabaseOperations() {
        // Start a conversation that requires database lookup
        ResponseEntity<ChatResponseDTO> response1 = sendChatMessage("Mark Ali absent today");
        
        assertEquals(HttpStatus.OK, response1.getStatusCode());
        assertTrue(response1.getBody().isSuccess());
        
        // Should suggest "Alice Johnson" as closest match
        String responseText1 = response1.getBody().getResponse().toLowerCase();
        assertTrue(responseText1.contains("alice") && responseText1.contains("did you mean"),
                "AI should suggest closest match from database");

        // Confirm the suggestion
        ResponseEntity<ChatResponseDTO> response2 = sendChatMessage("yes");
        
        assertEquals(HttpStatus.OK, response2.getStatusCode());
        assertTrue(response2.getBody().isSuccess());
        assertEquals("markAbsence", response2.getBody().getActionType());

        // Verify the absence was recorded for Alice Johnson
        Employee alice = employeeRepository.findAll().stream()
                .filter(e -> "Alice Johnson".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(alice);
        
        Optional<AbsenceRecord> absence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(alice.getId(), LocalDate.now());
        assertTrue(absence.isPresent(), "Absence should be recorded after confirmation");
        assertEquals(AbsenceRecord.AbsenceType.A, absence.get().getAbsenceType());
    }
}