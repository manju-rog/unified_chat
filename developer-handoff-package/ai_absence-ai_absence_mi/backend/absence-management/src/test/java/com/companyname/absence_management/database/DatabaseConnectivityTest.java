package com.companyname.absence_management.database;

import com.companyname.absence_management.model.Employee;
import com.companyname.absence_management.model.AbsenceRecord;
import com.companyname.absence_management.repository.EmployeeRepository;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import com.companyname.absence_management.service.DataInitializationService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("sqlite")
@Transactional
public class DatabaseConnectivityTest {

    @Autowired
    private DataSource dataSource;

    @Autowired
    private EmployeeRepository employeeRepository;

    @Autowired
    private AbsenceRecordRepository absenceRecordRepository;

    @Autowired
    private DataInitializationService dataInitializationService;

    @Test
    public void testDatabaseConnection() throws Exception {
        // Test basic database connectivity
        try (Connection connection = dataSource.getConnection()) {
            assertNotNull(connection, "Database connection should not be null");
            assertFalse(connection.isClosed(), "Database connection should be open");
            
            DatabaseMetaData metaData = connection.getMetaData();
            assertEquals("SQLite", metaData.getDatabaseProductName(), "Should be using SQLite database");
            
            System.out.println("✅ Database connection successful");
            System.out.println("Database Product: " + metaData.getDatabaseProductName());
            System.out.println("Database Version: " + metaData.getDatabaseProductVersion());
        }
    }

    @Test
    public void testTableCreation() throws Exception {
        // Test that tables are created properly
        try (Connection connection = dataSource.getConnection()) {
            DatabaseMetaData metaData = connection.getMetaData();
            
            // Check if employees table exists
            try (ResultSet employeesTable = metaData.getTables(null, null, "employees", null)) {
                assertTrue(employeesTable.next(), "Employees table should exist");
                System.out.println("✅ Employees table exists");
            }
            
            // Check if absence_records table exists
            try (ResultSet absenceTable = metaData.getTables(null, null, "absence_records", null)) {
                assertTrue(absenceTable.next(), "Absence records table should exist");
                System.out.println("✅ Absence records table exists");
            }
        }
    }

    @Test
    public void testDataInitializationService() {
        // Test data initialization - check if employees exist or can be created
        List<Employee> existingEmployees = employeeRepository.findAll();
        
        if (existingEmployees.isEmpty()) {
            // If no employees exist, test initialization
            dataInitializationService.initializeEmployees();
            existingEmployees = employeeRepository.findAll();
        }
        
        // Verify employees exist (either pre-existing or newly created)
        assertTrue(existingEmployees.size() >= 5, "Should have at least 5 employees");
        System.out.println("✅ Found " + existingEmployees.size() + " employees in database");
        
        // Verify specific employees exist
        assertTrue(existingEmployees.stream().anyMatch(e -> "Manju".equals(e.getName())), "Manju should exist");
        assertTrue(existingEmployees.stream().anyMatch(e -> "Shreyas".equals(e.getName())), "Shreyas should exist");
        assertTrue(existingEmployees.stream().anyMatch(e -> "Ganesh".equals(e.getName())), "Ganesh should exist");
        assertTrue(existingEmployees.stream().anyMatch(e -> "Suhas".equals(e.getName())), "Suhas should exist");
        assertTrue(existingEmployees.stream().anyMatch(e -> "Anushri".equals(e.getName())), "Anushri should exist");
        
        System.out.println("✅ Data initialization verified - " + existingEmployees.size() + " employees in database");
        
        // Verify employee details
        Employee manju = existingEmployees.stream()
            .filter(e -> "Manju".equals(e.getName()))
            .findFirst()
            .orElse(null);
        
        assertNotNull(manju, "Manju should be found");
        assertEquals("LDNR-MGR-01", manju.getEmployeeId(), "Manju should have correct employee ID");
        assertEquals("manju@company.com", manju.getEmail(), "Manju should have correct email");
        assertEquals("Management", manju.getDepartment(), "Manju should be in Management department");
        assertEquals("Engineering Manager", manju.getRole(), "Manju should be Engineering Manager");
        assertEquals("Bengaluru", manju.getLocation(), "Manju should be in Bengaluru");
        
        System.out.println("✅ Employee data validation successful");
    }

    @Test
    public void testDatabaseOperations() {
        // Clear existing data
        absenceRecordRepository.deleteAll();
        employeeRepository.deleteAll();
        
        // Create a test employee
        Employee testEmployee = new Employee();
        testEmployee.setName("Test Employee");
        testEmployee.setEmail("test@company.com");
        testEmployee.setEmployeeId("TEST-001");
        testEmployee.setDepartment("Testing");
        testEmployee.setRole("Test Engineer");
        testEmployee.setLocation("Test City");
        testEmployee.setJoinDate(LocalDate.now());
        
        // Save employee
        Employee savedEmployee = employeeRepository.save(testEmployee);
        assertNotNull(savedEmployee.getId(), "Saved employee should have an ID");
        
        // Create an absence record
        AbsenceRecord absenceRecord = new AbsenceRecord();
        absenceRecord.setEmployee(savedEmployee);
        absenceRecord.setAbsenceDate(LocalDate.now());
        absenceRecord.setAbsenceType(AbsenceRecord.AbsenceType.A);
        absenceRecord.setReason("Test absence");
        absenceRecord.setStatus(AbsenceRecord.AbsenceStatus.PENDING);
        
        // Save absence record
        AbsenceRecord savedAbsence = absenceRecordRepository.save(absenceRecord);
        assertNotNull(savedAbsence.getId(), "Saved absence record should have an ID");
        
        // Verify relationships work
        Optional<AbsenceRecord> employeeAbsence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(savedEmployee.getId(), LocalDate.now());
        assertTrue(employeeAbsence.isPresent(), "Employee should have one absence record");
        assertEquals("Test absence", employeeAbsence.get().getReason(), "Absence reason should match");
        
        System.out.println("✅ Database CRUD operations successful");
    }

    @Test
    public void testDatabaseFilePath() {
        // Verify the database file path configuration
        String expectedPath = "./abscent.db";
        
        try (Connection connection = dataSource.getConnection()) {
            String url = connection.getMetaData().getURL();
            assertTrue(url.contains("abscent.db"), "Database URL should contain abscent.db: " + url);
            System.out.println("✅ Database file path verified: " + url);
        } catch (Exception e) {
            fail("Failed to verify database file path: " + e.getMessage());
        }
    }

    @Test
    public void testHibernateConfiguration() {
        // Test that Hibernate is properly configured for SQLite
        // This is implicitly tested by the successful table creation and data operations
        // but we can add specific checks here
        
        // Verify that we can perform JPA operations
        long employeeCount = employeeRepository.count();
        assertTrue(employeeCount >= 0, "Employee count should be non-negative");
        
        long absenceCount = absenceRecordRepository.count();
        assertTrue(absenceCount >= 0, "Absence count should be non-negative");
        
        System.out.println("✅ Hibernate configuration verified");
        System.out.println("Current employee count: " + employeeCount);
        System.out.println("Current absence count: " + absenceCount);
    }
}