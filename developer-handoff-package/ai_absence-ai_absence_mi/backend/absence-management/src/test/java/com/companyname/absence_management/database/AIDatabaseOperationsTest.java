package com.companyname.absence_management.database;

import com.companyname.absence_management.model.Employee;
import com.companyname.absence_management.model.AbsenceRecord;
import com.companyname.absence_management.repository.EmployeeRepository;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import com.companyname.absence_management.services.EmployeeService;
import com.companyname.absence_management.services.AbsenceService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test class specifically focused on verifying that AI actions work correctly with database operations.
 * This test verifies that the AI can query employees from the SQLite database,
 * mark absences that are written to the database, and ensure all CRUD operations work correctly.
 */
@SpringBootTest
@ActiveProfiles("sqlite")
@Transactional
@DisplayName("AI Database Operations Tests")
public class AIDatabaseOperationsTest {

    @Autowired
    private EmployeeRepository employeeRepository;

    @Autowired
    private AbsenceRecordRepository absenceRecordRepository;

    @Autowired
    private EmployeeService employeeService;

    @Autowired
    private AbsenceService absenceService;

    @BeforeEach
    void setUp() {
        // Clear existing data
        absenceRecordRepository.deleteAll();
        employeeRepository.deleteAll();

        // Set up comprehensive test data for AI operations
        setupTestEmployees();
    }

    private void setupTestEmployees() {
        // Create diverse set of test employees that AI would interact with
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

    @Test
    @DisplayName("AI can query employees from SQLite database")
    void testAICanQueryEmployeesFromDatabase() {
        // Verify employees exist in database first
        List<Employee> allEmployees = employeeService.getAllEmployees();
        assertEquals(5, allEmployees.size(), "Should have 5 test employees in database");

        // Test that AI can access employee data by name (case-insensitive search)
        Optional<Employee> alice = allEmployees.stream()
                .filter(emp -> emp.getName().equalsIgnoreCase("alice johnson"))
                .findFirst();
        assertTrue(alice.isPresent(), "AI should be able to find Alice Johnson in database");
        assertEquals("alice.johnson@company.com", alice.get().getEmail());
        assertEquals("Engineering", alice.get().getDepartment());

        // Test partial name matching (what AI would do for fuzzy search)
        Optional<Employee> bob = allEmployees.stream()
                .filter(emp -> emp.getName().toLowerCase().contains("bob"))
                .findFirst();
        assertTrue(bob.isPresent(), "AI should be able to find Bob with partial name match");
        assertEquals("Bob Smith", bob.get().getName());

        // Test department-based queries (AI might query by department)
        List<Employee> engineeringEmployees = allEmployees.stream()
                .filter(emp -> "Engineering".equals(emp.getDepartment()))
                .toList();
        assertEquals(2, engineeringEmployees.size(), "Should find 2 engineering employees");
    }

    @Test
    @DisplayName("AI absence marking writes correctly to SQLite database")
    void testAIAbsenceMarkingWritesToDatabase() {
        // Get Diana for testing
        Employee diana = employeeRepository.findAll().stream()
                .filter(e -> "Diana Prince".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(diana, "Diana should exist in database");
        
        // Verify no absence exists for Diana today
        Optional<AbsenceRecord> beforeAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), LocalDate.now());
        assertFalse(beforeAbsence.isPresent(), "Diana should not have absence record for today initially");

        // Simulate AI marking Diana absent today using AbsenceService
        List<LocalDate> dates = List.of(LocalDate.now());
        absenceService.markAbsenceFromAI(diana.getId(), dates, "A", "Marked by AI Assistant");

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
        // Get Eve for testing
        Employee eve = employeeRepository.findAll().stream()
                .filter(e -> "Eve Wilson".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(eve, "Eve should exist in database");
        
        // Simulate AI marking Eve on vacation tomorrow
        LocalDate tomorrow = LocalDate.now().plusDays(1);
        List<LocalDate> dates = List.of(tomorrow);
        absenceService.markAbsenceFromAI(eve.getId(), dates, "V", "Vacation marked by AI");

        // Verify vacation was written to database
        Optional<AbsenceRecord> vacation = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(eve.getId(), tomorrow);
        assertTrue(vacation.isPresent(), "Vacation record should be created in database");
        assertEquals(AbsenceRecord.AbsenceType.V, vacation.get().getAbsenceType());
        assertEquals("Vacation marked by AI", vacation.get().getReason());
        assertEquals(AbsenceRecord.AbsenceStatus.APPROVED, vacation.get().getStatus());
    }

    @Test
    @DisplayName("AI can query historical absence data from database")
    void testAICanQueryHistoricalAbsenceData() {
        // Test querying who was absent yesterday (Alice should be found)
        LocalDate yesterday = LocalDate.now().minusDays(1);
        List<AbsenceRecord> yesterdayAbsences = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getAbsenceDate().equals(yesterday))
                .filter(record -> record.getAbsenceType() == AbsenceRecord.AbsenceType.A)
                .toList();
        
        assertEquals(1, yesterdayAbsences.size(), "Should find one absence yesterday");
        assertEquals("Alice Johnson", yesterdayAbsences.get(0).getEmployee().getName());
        assertEquals("Sick leave", yesterdayAbsences.get(0).getReason());
    }

    @Test
    @DisplayName("AI can query vacation data from database")
    void testAICanQueryVacationData() {
        // Test querying who was on vacation two days ago (Bob should be found)
        LocalDate twoDaysAgo = LocalDate.now().minusDays(2);
        List<AbsenceRecord> vacationRecords = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getAbsenceDate().equals(twoDaysAgo))
                .filter(record -> record.getAbsenceType() == AbsenceRecord.AbsenceType.V)
                .toList();
        
        assertEquals(1, vacationRecords.size(), "Should find one vacation record two days ago");
        assertEquals("Bob Smith", vacationRecords.get(0).getEmployee().getName());
        assertEquals("Personal vacation", vacationRecords.get(0).getReason());
    }

    @Test
    @DisplayName("AI handles database updates correctly - marking present removes absence")
    void testAIHandlesDatabaseUpdatesCorrectly() {
        // Get Charlie for testing
        Employee charlie = employeeRepository.findAll().stream()
                .filter(e -> "Charlie Brown".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(charlie, "Charlie should exist in database");
        
        // First mark Charlie absent today
        List<LocalDate> dates = List.of(LocalDate.now());
        absenceService.markAbsenceFromAI(charlie.getId(), dates, "A", "Test absence");

        // Verify absence was created
        Optional<AbsenceRecord> absence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(charlie.getId(), LocalDate.now());
        assertTrue(absence.isPresent(), "Absence should be created");

        // Now mark Charlie present (should remove the absence record)
        absenceService.markAbsenceFromAI(charlie.getId(), dates, "P", "Marked present");

        // Verify absence was removed from database
        Optional<AbsenceRecord> afterPresent = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(charlie.getId(), LocalDate.now());
        assertFalse(afterPresent.isPresent(), "Absence record should be removed when marked present");
    }

    @Test
    @DisplayName("AI handles multiple employee database operations")
    void testAIHandlesMultipleEmployeeDatabaseOperations() {
        // Get Alice and Bob for testing
        Employee alice = employeeRepository.findAll().stream()
                .filter(e -> "Alice Johnson".equals(e.getName()))
                .findFirst().orElse(null);
        Employee bob = employeeRepository.findAll().stream()
                .filter(e -> "Bob Smith".equals(e.getName()))
                .findFirst().orElse(null);
        
        assertNotNull(alice, "Alice should exist");
        assertNotNull(bob, "Bob should exist");
        
        // Mark both employees absent today
        List<LocalDate> dates = List.of(LocalDate.now());
        absenceService.markAbsenceFromAI(alice.getId(), dates, "A", "AI marked absent");
        absenceService.markAbsenceFromAI(bob.getId(), dates, "A", "AI marked absent");

        // Verify both absences were recorded in database
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
        // Get Diana for testing
        Employee diana = employeeRepository.findAll().stream()
                .filter(e -> "Diana Prince".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(diana, "Diana should exist");
        
        // Mark Diana absent for a range of dates (tomorrow to day after tomorrow)
        LocalDate tomorrow = LocalDate.now().plusDays(1);
        LocalDate dayAfter = LocalDate.now().plusDays(2);
        List<LocalDate> dates = List.of(tomorrow, dayAfter);
        
        absenceService.markAbsenceFromAI(diana.getId(), dates, "A", "AI marked range");

        // Verify multiple absence records were created in database
        Optional<AbsenceRecord> tomorrowAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), tomorrow);
        Optional<AbsenceRecord> dayAfterAbsence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(diana.getId(), dayAfter);
        
        assertTrue(tomorrowAbsence.isPresent(), "Tomorrow absence should be created");
        assertTrue(dayAfterAbsence.isPresent(), "Day after absence should be created");
        assertEquals(AbsenceRecord.AbsenceType.A, tomorrowAbsence.get().getAbsenceType());
        assertEquals(AbsenceRecord.AbsenceType.A, dayAfterAbsence.get().getAbsenceType());
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
        Employee alice = employeeRepository.findAll().stream()
                .filter(e -> "Alice Johnson".equals(e.getName()))
                .findFirst().orElse(null);
        Employee bob = employeeRepository.findAll().stream()
                .filter(e -> "Bob Smith".equals(e.getName()))
                .findFirst().orElse(null);
        
        List<LocalDate> dates = List.of(LocalDate.now());
        absenceService.markAbsenceFromAI(alice.getId(), dates, "A", "AI test");
        absenceService.markAbsenceFromAI(bob.getId(), dates, "V", "AI vacation");

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

        // Query for this specific absence (simulating AI query)
        List<AbsenceRecord> foundAbsences = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getAbsenceDate().equals(testDate))
                .filter(record -> record.getEmployee().getName().equals("Test Employee"))
                .toList();
        
        assertEquals(1, foundAbsences.size(), "Should find exactly one test absence");
        assertEquals("Test absence", foundAbsences.get(0).getReason());
        assertEquals(AbsenceRecord.AbsenceType.A, foundAbsences.get(0).getAbsenceType());
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

        // Test AI can handle complex names in database operations
        List<LocalDate> dates = List.of(LocalDate.now());
        absenceService.markAbsenceFromAI(complexNameEmployee.getId(), dates, "A", "Complex name test");

        // Verify the absence was recorded correctly
        Optional<AbsenceRecord> absence = absenceRecordRepository
                .findByEmployeeIdAndAbsenceDate(complexNameEmployee.getId(), LocalDate.now());
        assertTrue(absence.isPresent(), "Should handle complex employee names correctly");
        assertEquals(AbsenceRecord.AbsenceType.A, absence.get().getAbsenceType());
        assertEquals("María José García-López", absence.get().getEmployee().getName());
    }

    @Test
    @DisplayName("AI can perform complex database queries")
    void testAICanPerformComplexDatabaseQueries() {
        // Test complex queries that AI might perform
        
        // Query 1: Find all employees in Engineering department
        List<Employee> engineeringEmployees = employeeRepository.findAll().stream()
                .filter(emp -> "Engineering".equals(emp.getDepartment()))
                .toList();
        assertEquals(2, engineeringEmployees.size(), "Should find 2 engineering employees");
        
        // Query 2: Find all absences in the last week
        LocalDate oneWeekAgo = LocalDate.now().minusDays(7);
        List<AbsenceRecord> recentAbsences = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getAbsenceDate().isAfter(oneWeekAgo))
                .toList();
        assertTrue(recentAbsences.size() >= 2, "Should find recent absences");
        
        // Query 3: Find employees with no absences
        List<Employee> allEmployees = employeeRepository.findAll();
        List<AbsenceRecord> allAbsences = absenceRecordRepository.findAll();
        
        List<Employee> employeesWithoutAbsences = allEmployees.stream()
                .filter(emp -> allAbsences.stream()
                        .noneMatch(absence -> absence.getEmployee().getId().equals(emp.getId())))
                .toList();
        
        assertTrue(employeesWithoutAbsences.size() >= 2, "Should find employees without absences");
        
        // Query 4: Count absences by type
        long absentCount = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getAbsenceType() == AbsenceRecord.AbsenceType.A)
                .count();
        long vacationCount = absenceRecordRepository.findAll().stream()
                .filter(record -> record.getAbsenceType() == AbsenceRecord.AbsenceType.V)
                .count();
        
        assertTrue(absentCount > 0, "Should have some absent records");
        assertTrue(vacationCount > 0, "Should have some vacation records");
    }
}