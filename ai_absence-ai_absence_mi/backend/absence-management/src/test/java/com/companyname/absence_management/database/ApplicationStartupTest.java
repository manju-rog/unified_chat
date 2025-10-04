package com.companyname.absence_management.database;

import com.companyname.absence_management.repository.EmployeeRepository;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("sqlite")
public class ApplicationStartupTest {

    @Autowired
    private EmployeeRepository employeeRepository;

    @Autowired
    private AbsenceRecordRepository absenceRecordRepository;

    @Test
    public void testApplicationStartsSuccessfully() {
        // Test that the application context loads successfully
        assertNotNull(employeeRepository, "EmployeeRepository should be autowired");
        assertNotNull(absenceRecordRepository, "AbsenceRecordRepository should be autowired");
        
        System.out.println("✅ Application started successfully with SQLite profile");
    }

    @Test
    public void testDatabaseTablesExistAndHaveData() {
        // Test that tables exist and have data
        long employeeCount = employeeRepository.count();
        long absenceCount = absenceRecordRepository.count();
        
        assertTrue(employeeCount > 0, "Employee table should have data");
        assertTrue(absenceCount >= 0, "Absence records table should exist (may be empty)");
        
        System.out.println("✅ Database tables verified:");
        System.out.println("   - Employees: " + employeeCount);
        System.out.println("   - Absence Records: " + absenceCount);
    }

    @Test
    public void testDataInitializationServiceRan() {
        // Verify that the DataInitializationService has run and created the expected employees
        long employeeCount = employeeRepository.count();
        
        assertEquals(5, employeeCount, "Should have exactly 5 employees from DataInitializationService");
        
        // Verify specific employees exist
        assertTrue(employeeRepository.findAll().stream()
            .anyMatch(e -> "Manju".equals(e.getName())), "Manju should exist");
        assertTrue(employeeRepository.findAll().stream()
            .anyMatch(e -> "Shreyas".equals(e.getName())), "Shreyas should exist");
        assertTrue(employeeRepository.findAll().stream()
            .anyMatch(e -> "Ganesh".equals(e.getName())), "Ganesh should exist");
        assertTrue(employeeRepository.findAll().stream()
            .anyMatch(e -> "Suhas".equals(e.getName())), "Suhas should exist");
        assertTrue(employeeRepository.findAll().stream()
            .anyMatch(e -> "Anushri".equals(e.getName())), "Anushri should exist");
        
        System.out.println("✅ DataInitializationService verification successful");
    }
}