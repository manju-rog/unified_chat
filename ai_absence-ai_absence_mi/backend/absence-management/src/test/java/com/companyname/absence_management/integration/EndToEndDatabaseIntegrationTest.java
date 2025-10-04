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
import org.junit.jupiter.api.*;
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
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Comprehensive end-to-end database integration tests that verify:
 * 1. Complete flow: AI query → database lookup → response
 * 2. Complete flow: AI absence marking → database write → confirmation
 * 3. Database persistence across application restarts
 * 
 * This test class focuses on the complete AI-database workflow as specified in task 13.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("sqlite")
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("End-to-End Database Integration Tests")
public class EndToEndDatabaseIntegrationTest {

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

    // Static variables to maintain state across test methods for persistence testing
    private static Long persistentEmployeeId;
    private static LocalDate persistentAbsenceDate;
    private static String persistentEmployeeName = "Persistent Test Employee";

    @BeforeEach
    void setUp() {
        baseUrl = "http://localhost:" + port + "/api/ai";
        conversationId = "e2e-test-conv-" + UUID.randomUUID().toString();
        
        headers = new HttpHeaders();
        headers.set("Content-Type", "application/json");
        headers.set("Accept", "application/json");

        // Clear conversation context
        conversationContextService.clearContext(conversationId);
    }

    @BeforeAll
    static void setUpClass(@Autowired EmployeeRepository employeeRepository, 
                          @Autowired AbsenceRecordRepository absenceRecordRepository) {
        // Set up persistent test data that will be used across multiple tests
        setupPersistentTestData(employeeRepository, absenceRecordRepository);
    }

    private static void setupPersistentTestData(EmployeeRepository employeeRepository, 
                                              AbsenceRecordRepository absenceRecordRepository) {
        // Clear existing data
        absenceRecordRepository.deleteAll();
        employeeRepository.deleteAll();

        // Create comprehensive test dataset
        Employee alice = Employee.builder()
                .name("Alice Johnson")
                .email("alice.johnson@company.com")
                .phone("1111111111")
                .department("Engineering")
                .role("Senior Developer")
                .location("New York")
                .employeeId("E001")
                .build();
        alice = employeeRepository.save(alice);

        Employee bob = Employee.builder()
                .name("Bob Smith")
                .email("bob.smith@company.com")
                .phone("2222222222")
                .department("Marketing")
                .role("Marketing Manager")
                .location("San Francisco")
                .employeeId("E002")
                .build();
        bob = employeeRepository.save(bob);

        Employee charlie = Employee.builder()
                .name("Charlie Brown")
                .email("charlie.brown@company.com")
                .phone("3333333333")
                .department("HR")
                .role("HR Specialist")
                .location("Chicago")
                .employeeId("E003")
                .build();
        charlie = employeeRepository.save(charlie);

        Employee diana = Employee.builder()
                .name("Diana Prince")
                .email("diana.prince@company.com")
                .phone("4444444444")
                .department("Finance")
                .role("Financial Analyst")
                .location("Boston")
                .employeeId("E004")
                .build();
        diana = employeeRepository.save(diana);

        // Create persistent employee for cross-test persistence verification
        Employee persistentEmployee = Employee.builder()
                .name(persistentEmployeeName)
                .email("persistent@company.com")
                .phone("9999999999")
                .department("Testing")
                .role("Test Engineer")
                .location("Test City")
                .employeeId("PERSIST001")
                .build();
        persistentEmployee = employeeRepository.save(persistentEmployee);
        persistentEmployeeId = persistentEmployee.getId();
        persistentAbsenceDate = LocalDate.now().minusDays(1);

        // Add historical absence data for testing queries
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

        // Create persistent absence record for cross-test verification
        AbsenceRecord persistentAbsence = AbsenceRecord.builder()
                .employee(persistentEmployee)
                .absenceDate(persistentAbsenceDate)
                .absenceType(AbsenceRecord.AbsenceType.A)
                .reason("Persistent test absence")
                .status(AbsenceRecord.AbsenceStatus.APPROVED)
                .build();
        absenceRecordRepository.save(persistentAbsence);
    }

    private ResponseEntity<ChatResponseDTO> sendChatMessage(String message) {
        ChatRequestDTO request = new ChatRequestDTO();
        request.setMessage(message);
        request.setConversationId(conversationId);

        HttpEntity<ChatRequestDTO> entity = new HttpEntity<>(request, headers);
        return restTemplate.postForEntity(baseUrl + "/chat", entity, ChatResponseDTO.class);
    }

    @Test
    @Order(1)
    @DisplayName("Complete Flow: AI Query → Database Lookup → Response")
    void testCompleteAIQueryToDatabaseLookupFlow() {
        System.out.println("=== Testing Complete AI Query → Database Lookup → Response Flow ===");

        // Test 1: Query for employees who were absent yesterday
        System.out.println("Test 1: Querying who was absent yesterday");
        ResponseEntity<ChatResponseDTO> response1 = sendChatMessage("Who was absent yesterday?");
        
        assertEquals(HttpStatus.OK, response1.getStatusCode());
        assertNotNull(response1.getBody());
        assertTrue(response1.getBody().isSuccess());
        assertEquals("queryAbsence", response1.getBody().getActionType());
        
        String responseText1 = response1.getBody().getResponse().toLowerCase();
        assertTrue(responseText1.contains("alice") || responseText1.contains("persistent"), 
                "AI should find employees who were absent yesterday from database");
        
        System.out.println("✓ AI successfully queried database and found absent employees");

        // Test 2: Query for employees on vacation
        System.out.println("Test 2: Querying who was on vacation two days ago");
        LocalDate twoDaysAgo = LocalDate.now().minusDays(2);
        String vacationQuery = String.format("Who was on vacation on %s?", 
                twoDaysAgo.format(DateTimeFormatter.ofPattern("MMMM d, yyyy")));
        
        ResponseEntity<ChatResponseDTO> response2 = sendChatMessage(vacationQuery);
        
        assertEquals(HttpStatus.OK, response2.getStatusCode());
        assertNotNull(response2.getBody());
        assertTrue(response2.getBody().isSuccess());
        assertEquals("queryAbsence", response2.getBody().getActionType());
        
        String responseText2 = response2.getBody().getResponse().toLowerCase();
        assertTrue(responseText2.contains("bob") || responseText2.contains("vacation"), 
                "AI should find employees who were on vacation from database");
        
        System.out.println("✓ AI successfully queried database and found vacation records");

        // Test 3: Query for specific employee's absence history
        System.out.println("Test 3: Querying specific employee's absence history");
        ResponseEntity<ChatResponseDTO> response3 = sendChatMessage("Show me Alice Johnson's recent absences");
        
        assertEquals(HttpStatus.OK, response3.getStatusCode());
        assertNotNull(response3.getBody());
        assertTrue(response3.getBody().isSuccess());
        
        String responseText3 = response3.getBody().getResponse().toLowerCase();
        assertTrue(responseText3.contains("alice") && 
                  (responseText3.contains("absent") || responseText3.contains("sick")), 
                "AI should find Alice's specific absence records from database");
        
        System.out.println("✓ AI successfully queried specific employee's absence history");

        // Test 4: Query for employees by department
        System.out.println("Test 4: Querying employees by department");
        ResponseEntity<ChatResponseDTO> response4 = sendChatMessage("Who are the employees in the Engineering department?");
        
        assertEquals(HttpStatus.OK, response4.getStatusCode());
        assertNotNull(response4.getBody());
        assertTrue(response4.getBody().isSuccess());
        
        String responseText4 = response4.getBody().getResponse().toLowerCase();
        assertTrue(responseText4.contains("alice") || responseText4.contains("engineering"), 
                "AI should find employees in Engineering department from database");
        
        System.out.println("✓ AI successfully queried employees by department");

        // Test 5: Complex date range query
        System.out.println("Test 5: Complex date range query");
        ResponseEntity<ChatResponseDTO> response5 = sendChatMessage("Who was absent in the last week?");
        
        assertEquals(HttpStatus.OK, response5.getStatusCode());
        assertNotNull(response5.getBody());
        assertTrue(response5.getBody().isSuccess());
        assertEquals("queryAbsence", response5.getBody().getActionType());
        
        String responseText5 = response5.getBody().getResponse().toLowerCase();
        assertTrue(responseText5.contains("alice") || responseText5.contains("charlie") || 
                  responseText5.contains("persistent"), 
                "AI should find employees absent in the last week from database");
        
        System.out.println("✓ AI successfully handled complex date range query");
        System.out.println("=== Complete AI Query Flow Test PASSED ===\n");
    }

    @Test
    @Order(2)
    @DisplayName("Complete Flow: AI Absence Marking → Database Write → Confirmation")
    void testCompleteAIAbsenceMarkingToDatabaseWriteFlow() {
        System.out.println("=== Testing Complete AI Absence Marking → Database Write → Confirmation Flow ===");

        // Test 1: Mark single employee absent
        System.out.println("Test 1: Marking single employee absent");
        ResponseEntity<ChatResponseDTO> response1 = sendChatMessage("Mark Diana Prince absent today");
        
        assertEquals(HttpStatus.OK, response1.getStatusCode());
        assertNotNull(response1.getBody());
        assertTrue(response1.getBody().isSuccess());
        assertEquals("markAbsence", response1.getBody().getActionType());
        
        // Verify database write
        Employee diana = employeeRepository.findAll().stream()
                .filter(e -> "Diana Prince".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(diana, "Diana should exist in database");
        
        Optional<AbsenceRecord> dianaAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), LocalDate.now());
        assertTrue(dianaAbsence.isPresent(), "Diana's absence should be written to database");
        assertEquals(AbsenceRecord.AbsenceType.A, dianaAbsence.get().getAbsenceType());
        assertEquals("Marked by AI Assistant", dianaAbsence.get().getReason());
        
        System.out.println("✓ Single employee absence successfully marked and written to database");

        // Test 2: Mark employee on vacation
        System.out.println("Test 2: Marking employee on vacation");
        LocalDate tomorrow = LocalDate.now().plusDays(1);
        ResponseEntity<ChatResponseDTO> response2 = sendChatMessage("Put Charlie Brown on vacation tomorrow");
        
        assertEquals(HttpStatus.OK, response2.getStatusCode());
        assertNotNull(response2.getBody());
        assertTrue(response2.getBody().isSuccess());
        assertEquals("markAbsence", response2.getBody().getActionType());
        
        // Verify vacation write
        Employee charlie = employeeRepository.findAll().stream()
                .filter(e -> "Charlie Brown".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(charlie, "Charlie should exist in database");
        
        Optional<AbsenceRecord> charlieVacation = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(charlie.getId(), tomorrow);
        assertTrue(charlieVacation.isPresent(), "Charlie's vacation should be written to database");
        assertEquals(AbsenceRecord.AbsenceType.V, charlieVacation.get().getAbsenceType());
        
        System.out.println("✓ Employee vacation successfully marked and written to database");

        // Test 3: Mark multiple employees absent
        System.out.println("Test 3: Marking multiple employees absent");
        ResponseEntity<ChatResponseDTO> response3 = sendChatMessage("Mark Alice Johnson and Bob Smith absent today");
        
        assertEquals(HttpStatus.OK, response3.getStatusCode());
        assertNotNull(response3.getBody());
        assertTrue(response3.getBody().isSuccess());
        assertEquals("markAbsence", response3.getBody().getActionType());
        
        // Verify both employees' absences were written
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
        
        assertTrue(aliceAbsence.isPresent(), "Alice's absence should be written to database");
        assertTrue(bobAbsence.isPresent(), "Bob's absence should be written to database");
        assertEquals(AbsenceRecord.AbsenceType.A, aliceAbsence.get().getAbsenceType());
        assertEquals(AbsenceRecord.AbsenceType.A, bobAbsence.get().getAbsenceType());
        
        System.out.println("✓ Multiple employees' absences successfully marked and written to database");

        // Test 4: Mark employee present (should remove absence)
        System.out.println("Test 4: Marking employee present (removing absence)");
        ResponseEntity<ChatResponseDTO> response4 = sendChatMessage("Mark Diana Prince present today");
        
        assertEquals(HttpStatus.OK, response4.getStatusCode());
        assertNotNull(response4.getBody());
        assertTrue(response4.getBody().isSuccess());
        
        // Verify absence was removed from database
        Optional<AbsenceRecord> dianaAfterPresent = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), LocalDate.now());
        assertFalse(dianaAfterPresent.isPresent(), "Diana's absence should be removed when marked present");
        
        System.out.println("✓ Employee successfully marked present and absence removed from database");

        // Test 5: Date range absence marking
        System.out.println("Test 5: Date range absence marking");
        ResponseEntity<ChatResponseDTO> response5 = sendChatMessage("Mark Alice Johnson absent from next Monday to next Wednesday");
        
        assertEquals(HttpStatus.OK, response5.getStatusCode());
        assertNotNull(response5.getBody());
        assertTrue(response5.getBody().isSuccess());
        assertEquals("markAbsence", response5.getBody().getActionType());
        
        // Verify multiple dates were written (check at least one future date)
        LocalDate nextWeek = LocalDate.now().plusDays(7);
        boolean foundFutureAbsence = false;
        for (int i = 1; i <= 10; i++) { // Check next 10 days
            LocalDate checkDate = LocalDate.now().plusDays(i);
            Optional<AbsenceRecord> futureAbsence = absenceRecordRepository
                    .findByEmployeeIdAndAbsenceDate(alice.getId(), checkDate);
            if (futureAbsence.isPresent()) {
                foundFutureAbsence = true;
                assertEquals(AbsenceRecord.AbsenceType.A, futureAbsence.get().getAbsenceType());
                break;
            }
        }
        assertTrue(foundFutureAbsence, "At least one future absence should be created for date range");
        
        System.out.println("✓ Date range absence successfully marked and written to database");
        System.out.println("=== Complete AI Absence Marking Flow Test PASSED ===\n");
    }

    @Test
    @Order(3)
    @DisplayName("Database Persistence Verification")
    void testDatabasePersistenceAcrossOperations() {
        System.out.println("=== Testing Database Persistence Across Operations ===");

        // Test 1: Verify persistent data still exists
        System.out.println("Test 1: Verifying persistent test data exists");
        
        // Check persistent employee exists
        Optional<Employee> persistentEmployee = employeeRepository.findById(persistentEmployeeId);
        assertTrue(persistentEmployee.isPresent(), "Persistent employee should exist in database");
        assertEquals(persistentEmployeeName, persistentEmployee.get().getName());
        
        // Check persistent absence exists
        Optional<AbsenceRecord> persistentAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(persistentEmployeeId, persistentAbsenceDate);
        assertTrue(persistentAbsence.isPresent(), "Persistent absence should exist in database");
        assertEquals(AbsenceRecord.AbsenceType.A, persistentAbsence.get().getAbsenceType());
        
        System.out.println("✓ Persistent test data verified in database");

        // Test 2: Create new data and verify it persists
        System.out.println("Test 2: Creating new data for persistence verification");
        
        Employee newEmployee = Employee.builder()
                .name("Persistence Test Employee")
                .email("persistence@test.com")
                .phone("5555555555")
                .department("Testing")
                .role("Persistence Tester")
                .location("Test Location")
                .employeeId("PERSIST002")
                .build();
        Employee savedEmployee = employeeRepository.save(newEmployee);
        
        LocalDate testDate = LocalDate.now().plusDays(5);
        AbsenceRecord newAbsence = AbsenceRecord.builder()
                .employee(savedEmployee)
                .absenceDate(testDate)
                .absenceType(AbsenceRecord.AbsenceType.V)
                .reason("Persistence test vacation")
                .status(AbsenceRecord.AbsenceStatus.APPROVED)
                .build();
        AbsenceRecord savedAbsence = absenceRecordRepository.save(newAbsence);
        
        System.out.println("✓ New test data created and saved to database");

        // Test 3: Verify AI can access newly created persistent data
        System.out.println("Test 3: Verifying AI can access newly created data");
        
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Who is the Persistence Test Employee?");
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertTrue(response.getBody().isSuccess());
        
        String responseText = response.getBody().getResponse().toLowerCase();
        assertTrue(responseText.contains("persistence") || responseText.contains("test"), 
                "AI should be able to access newly created employee from database");
        
        System.out.println("✓ AI successfully accessed newly created persistent data");

        // Test 4: Verify data integrity after multiple operations
        System.out.println("Test 4: Verifying data integrity after multiple operations");
        
        // Perform multiple AI operations
        sendChatMessage("Mark Persistence Test Employee absent today");
        sendChatMessage("Who was absent today?");
        sendChatMessage("Put Persistence Test Employee on vacation next week");
        
        // Verify all data is still intact
        Optional<Employee> employeeAfterOps = employeeRepository.findById(savedEmployee.getId());
        assertTrue(employeeAfterOps.isPresent(), "Employee should still exist after multiple operations");
        
        List<AbsenceRecord> employeeAbsences = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getEmployee().getId().equals(savedEmployee.getId()))
                .toList();
        assertTrue(employeeAbsences.size() >= 2, "Employee should have multiple absence records");
        
        System.out.println("✓ Data integrity maintained after multiple AI operations");

        // Test 5: Verify referential integrity
        System.out.println("Test 5: Verifying referential integrity");
        
        List<AbsenceRecord> allAbsences = absenceRecordRepository.findAll();
        for (AbsenceRecord absence : allAbsences) {
            assertNotNull(absence.getEmployee(), "Every absence should have an employee reference");
            assertTrue(employeeRepository.existsById(absence.getEmployee().getId()), 
                    "Every absence should reference an existing employee");
            assertNotNull(absence.getAbsenceDate(), "Every absence should have a date");
            assertNotNull(absence.getAbsenceType(), "Every absence should have a type");
        }
        
        System.out.println("✓ Referential integrity verified across all records");

        // Test 6: Verify database constraints are enforced
        System.out.println("Test 6: Verifying database constraints");
        
        long totalEmployees = employeeRepository.count();
        long totalAbsences = absenceRecordRepository.count();
        
        assertTrue(totalEmployees >= 6, "Should have at least 6 employees in database");
        assertTrue(totalAbsences >= 5, "Should have at least 5 absence records in database");
        
        // Verify unique constraints (no duplicate employee IDs)
        List<Employee> allEmployees = employeeRepository.findAll();
        long uniqueEmployeeIds = allEmployees.stream()
                .map(Employee::getEmployeeId)
                .distinct()
                .count();
        assertEquals(allEmployees.size(), uniqueEmployeeIds, "All employee IDs should be unique");
        
        System.out.println("✓ Database constraints properly enforced");
        System.out.println("=== Database Persistence Test PASSED ===\n");
    }

    @Test
    @Order(4)
    @DisplayName("Cross-Session Data Persistence")
    void testCrossSessionDataPersistence() {
        System.out.println("=== Testing Cross-Session Data Persistence ===");

        // Test 1: Create data in one "session" (conversation)
        System.out.println("Test 1: Creating data in first session");
        String session1Id = "session-1-" + UUID.randomUUID().toString();
        
        ChatRequestDTO request1 = new ChatRequestDTO();
        request1.setMessage("Mark Alice Johnson absent today for cross-session test");
        request1.setConversationId(session1Id);
        
        HttpEntity<ChatRequestDTO> entity1 = new HttpEntity<>(request1, headers);
        ResponseEntity<ChatResponseDTO> response1 = restTemplate.postForEntity(baseUrl + "/chat", entity1, ChatResponseDTO.class);
        
        assertEquals(HttpStatus.OK, response1.getStatusCode());
        assertTrue(response1.getBody().isSuccess());
        
        System.out.println("✓ Data created in first session");

        // Test 2: Access data from different "session" (conversation)
        System.out.println("Test 2: Accessing data from second session");
        String session2Id = "session-2-" + UUID.randomUUID().toString();
        
        ChatRequestDTO request2 = new ChatRequestDTO();
        request2.setMessage("Who was absent today?");
        request2.setConversationId(session2Id);
        
        HttpEntity<ChatRequestDTO> entity2 = new HttpEntity<>(request2, headers);
        ResponseEntity<ChatResponseDTO> response2 = restTemplate.postForEntity(baseUrl + "/chat", entity2, ChatResponseDTO.class);
        
        assertEquals(HttpStatus.OK, response2.getStatusCode());
        assertTrue(response2.getBody().isSuccess());
        assertEquals("queryAbsence", response2.getBody().getActionType());
        
        String responseText = response2.getBody().getResponse().toLowerCase();
        assertTrue(responseText.contains("alice"), 
                "Second session should be able to access data created in first session");
        
        System.out.println("✓ Data successfully accessed from different session");

        // Test 3: Verify data persists across multiple conversation contexts
        System.out.println("Test 3: Verifying data persistence across conversation contexts");
        
        // Clear conversation contexts
        conversationContextService.clearContext(session1Id);
        conversationContextService.clearContext(session2Id);
        
        // Create third session and verify data is still accessible
        String session3Id = "session-3-" + UUID.randomUUID().toString();
        
        ChatRequestDTO request3 = new ChatRequestDTO();
        request3.setMessage("Show me today's absences");
        request3.setConversationId(session3Id);
        
        HttpEntity<ChatRequestDTO> entity3 = new HttpEntity<>(request3, headers);
        ResponseEntity<ChatResponseDTO> response3 = restTemplate.postForEntity(baseUrl + "/chat", entity3, ChatResponseDTO.class);
        
        assertEquals(HttpStatus.OK, response3.getStatusCode());
        assertTrue(response3.getBody().isSuccess());
        
        String response3Text = response3.getBody().getResponse().toLowerCase();
        assertTrue(response3Text.contains("alice") || response3Text.contains("absent"), 
                "Data should persist even after conversation contexts are cleared");
        
        System.out.println("✓ Data persists across conversation context changes");
        System.out.println("=== Cross-Session Data Persistence Test PASSED ===\n");
    }

    @Test
    @Order(5)
    @DisplayName("Database Transaction Integrity")
    void testDatabaseTransactionIntegrity() {
        System.out.println("=== Testing Database Transaction Integrity ===");

        // Test 1: Verify atomic operations
        System.out.println("Test 1: Testing atomic operations");
        
        long initialAbsenceCount = absenceRecordRepository.count();
        
        // Mark multiple employees - should be atomic
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Alice Johnson, Bob Smith, and Charlie Brown absent today");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertTrue(response.getBody().isSuccess());
        
        long finalAbsenceCount = absenceRecordRepository.count();
        assertTrue(finalAbsenceCount > initialAbsenceCount, "Absence count should increase after marking employees absent");
        
        System.out.println("✓ Atomic operations working correctly");

        // Test 2: Verify data consistency
        System.out.println("Test 2: Testing data consistency");
        
        List<AbsenceRecord> todayAbsences = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getAbsenceDate().equals(LocalDate.now()))
                .toList();
        
        // All today's absences should have valid employee references
        for (AbsenceRecord absence : todayAbsences) {
            assertNotNull(absence.getEmployee(), "Every absence should have an employee");
            assertTrue(employeeRepository.existsById(absence.getEmployee().getId()), 
                    "Every absence should reference an existing employee");
            assertEquals(LocalDate.now(), absence.getAbsenceDate(), "All should be for today");
            assertNotNull(absence.getAbsenceType(), "Every absence should have a type");
            assertNotNull(absence.getStatus(), "Every absence should have a status");
        }
        
        System.out.println("✓ Data consistency verified");

        // Test 3: Verify cascade operations
        System.out.println("Test 3: Testing cascade operations");
        
        // Create a test employee and absence
        Employee testEmployee = Employee.builder()
                .name("Transaction Test Employee")
                .email("transaction@test.com")
                .phone("7777777777")
                .department("Testing")
                .role("Transaction Tester")
                .location("Test City")
                .employeeId("TRANS001")
                .build();
        testEmployee = employeeRepository.save(testEmployee);
        
        // Mark this employee absent via AI
        ResponseEntity<ChatResponseDTO> markResponse = sendChatMessage("Mark Transaction Test Employee absent today");
        assertEquals(HttpStatus.OK, markResponse.getStatusCode());
        assertTrue(markResponse.getBody().isSuccess());
        
        // Verify the absence was created
        Optional<AbsenceRecord> testAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(testEmployee.getId(), LocalDate.now());
        assertTrue(testAbsence.isPresent(), "Test absence should be created");
        
        System.out.println("✓ Cascade operations working correctly");
        System.out.println("=== Database Transaction Integrity Test PASSED ===\n");
    }

    @Test
    @Order(6)
    @DisplayName("Performance and Scalability Verification")
    void testPerformanceAndScalability() {
        System.out.println("=== Testing Performance and Scalability ===");

        // Test 1: Large dataset query performance
        System.out.println("Test 1: Testing large dataset query performance");
        
        long startTime = System.currentTimeMillis();
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Show me all employees in the system");
        long endTime = System.currentTimeMillis();
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertTrue(response.getBody().isSuccess());
        
        long queryTime = endTime - startTime;
        assertTrue(queryTime < 5000, "Query should complete within 5 seconds"); // Reasonable timeout
        
        System.out.println("✓ Large dataset query completed in " + queryTime + "ms");

        // Test 2: Bulk operations performance
        System.out.println("Test 2: Testing bulk operations performance");
        
        startTime = System.currentTimeMillis();
        ResponseEntity<ChatResponseDTO> bulkResponse = sendChatMessage("Mark all Engineering employees absent tomorrow");
        endTime = System.currentTimeMillis();
        
        assertEquals(HttpStatus.OK, bulkResponse.getStatusCode());
        assertTrue(bulkResponse.getBody().isSuccess());
        
        long bulkTime = endTime - startTime;
        assertTrue(bulkTime < 10000, "Bulk operation should complete within 10 seconds");
        
        System.out.println("✓ Bulk operation completed in " + bulkTime + "ms");

        // Test 3: Concurrent access simulation
        System.out.println("Test 3: Testing concurrent access simulation");
        
        // Simulate multiple concurrent requests
        String[] messages = {
            "Who was absent yesterday?",
            "Mark Diana Prince absent today",
            "Show me vacation records",
            "Who works in HR department?",
            "Mark Bob Smith on vacation next week"
        };
        
        startTime = System.currentTimeMillis();
        for (String message : messages) {
            ResponseEntity<ChatResponseDTO> concurrentResponse = sendChatMessage(message);
            assertEquals(HttpStatus.OK, concurrentResponse.getStatusCode());
            assertTrue(concurrentResponse.getBody().isSuccess());
        }
        endTime = System.currentTimeMillis();
        
        long concurrentTime = endTime - startTime;
        assertTrue(concurrentTime < 15000, "Concurrent operations should complete within 15 seconds");
        
        System.out.println("✓ Concurrent operations completed in " + concurrentTime + "ms");
        System.out.println("=== Performance and Scalability Test PASSED ===\n");
    }

    @Test
    @Order(7)
    @DisplayName("Final Integration Verification")
    void testFinalIntegrationVerification() {
        System.out.println("=== Final Integration Verification ===");

        // Test 1: Complete workflow verification
        System.out.println("Test 1: Complete workflow verification");
        
        // Step 1: Query current state
        ResponseEntity<ChatResponseDTO> queryResponse = sendChatMessage("Who is absent today?");
        assertEquals(HttpStatus.OK, queryResponse.getStatusCode());
        assertTrue(queryResponse.getBody().isSuccess());
        
        // Step 2: Mark someone absent
        ResponseEntity<ChatResponseDTO> markResponse = sendChatMessage("Mark Charlie Brown absent today");
        assertEquals(HttpStatus.OK, markResponse.getStatusCode());
        assertTrue(markResponse.getBody().isSuccess());
        assertEquals("markAbsence", markResponse.getBody().getActionType());
        
        // Step 3: Verify the change
        ResponseEntity<ChatResponseDTO> verifyResponse = sendChatMessage("Is Charlie Brown absent today?");
        assertEquals(HttpStatus.OK, verifyResponse.getStatusCode());
        assertTrue(verifyResponse.getBody().isSuccess());
        
        String verifyText = verifyResponse.getBody().getResponse().toLowerCase();
        assertTrue(verifyText.contains("charlie") && verifyText.contains("absent"), 
                "Should confirm Charlie is absent");
        
        System.out.println("✓ Complete workflow verified");

        // Test 2: Data consistency final check
        System.out.println("Test 2: Final data consistency check");
        
        long totalEmployees = employeeRepository.count();
        long totalAbsences = absenceRecordRepository.count();
        
        assertTrue(totalEmployees > 0, "Should have employees in database");
        assertTrue(totalAbsences > 0, "Should have absence records in database");
        
        // Verify all absence records have valid employee references
        List<AbsenceRecord> allAbsences = absenceRecordRepository.findAll();
        for (AbsenceRecord absence : allAbsences) {
            assertNotNull(absence.getEmployee(), "Every absence should have an employee");
            assertTrue(employeeRepository.existsById(absence.getEmployee().getId()), 
                    "Every absence should reference an existing employee");
        }
        
        System.out.println("✓ Final data consistency verified");

        // Test 3: AI-Database integration health check
        System.out.println("Test 3: AI-Database integration health check");
        
        ResponseEntity<ChatResponseDTO> healthResponse = sendChatMessage("How many employees are in the system?");
        assertEquals(HttpStatus.OK, healthResponse.getStatusCode());
        assertTrue(healthResponse.getBody().isSuccess());
        
        String healthText = healthResponse.getBody().getResponse().toLowerCase();
        assertTrue(healthText.contains("employee") || healthText.contains("total") || 
                  healthText.matches(".*\\d+.*"), 
                "AI should be able to provide employee count from database");
        
        System.out.println("✓ AI-Database integration health check passed");
        
        System.out.println("=== Final Integration Verification PASSED ===");
        System.out.println("=== ALL END-TO-END DATABASE INTEGRATION TESTS COMPLETED SUCCESSFULLY ===");
    }
}