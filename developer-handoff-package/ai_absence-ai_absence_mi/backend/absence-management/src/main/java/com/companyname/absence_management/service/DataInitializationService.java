package com.companyname.absence_management.service;

import com.companyname.absence_management.model.Employee;
import com.companyname.absence_management.repository.EmployeeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

@Service
public class DataInitializationService implements CommandLineRunner {

    @Autowired
    private EmployeeRepository employeeRepository;

    @Override
    public void run(String... args) throws Exception {
        // Only initialize if database is empty
        if (employeeRepository.count() == 0) {
            initializeEmployees();
        }
    }

    public void initializeEmployees() {
        List<Employee> employees = Arrays.asList(
            createEmployee("LDNR-MGR-01", "Manju", "manju@company.com", "Management", "Engineering Manager", "Bengaluru"),
            createEmployee("LDNR-DEV-02", "Shreyas", "shreyas@company.com", "Development", "Senior Developer", "Bengaluru"),
            createEmployee("LDNR-DEV-03", "Ganesh", "ganesh@company.com", "Development", "Full Stack Developer", "Bengaluru"),
            createEmployee("LDNR-DEV-04", "Suhas", "suhas@company.com", "Development", "Tech Lead", "Bengaluru"),
            createEmployee("LDNR-QA-05", "Anushri", "anushri@company.com", "Quality Assurance", "QA Lead", "Bengaluru")
        );

        employeeRepository.saveAll(employees);
        System.out.println("✅ Initialized " + employees.size() + " employees in the database");
    }

    private Employee createEmployee(String employeeId, String name, String email, String department, String role, String location) {
        Employee employee = new Employee();
        employee.setEmployeeId(employeeId);
        employee.setName(name);
        employee.setEmail(email);
        employee.setDepartment(department);
        employee.setRole(role);
        employee.setLocation(location);
        employee.setJoinDate(LocalDate.now().minusMonths((long) (Math.random() * 24))); // Random join date within last 2 years
        return employee;
    }
}