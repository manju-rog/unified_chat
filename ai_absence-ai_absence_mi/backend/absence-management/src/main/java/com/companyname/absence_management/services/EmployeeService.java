package com.companyname.absence_management.services;

import com.companyname.absence_management.exception.EmployeeEmailAlreadyExistsException;
import com.companyname.absence_management.exception.EmployeeIdAlreadyExistsException;
import com.companyname.absence_management.exception.EmployeePhoneAlreadyExistsException;
import com.companyname.absence_management.model.Employee;
import com.companyname.absence_management.repository.EmployeeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class EmployeeService {

    @Autowired
    private EmployeeRepository employeeRepository;

    public Employee addEmployee(Employee employee) {
        if (employeeRepository.existsByEmployeeId(employee.getEmployeeId())) {
            throw new EmployeeIdAlreadyExistsException("Employee ID already exists");
        }
        if (employeeRepository.existsByEmail(employee.getEmail())) {
            throw new EmployeeEmailAlreadyExistsException("Email ID already exists");
        }
        if (employee.getPhone() != null && employeeRepository.existsByPhone(employee.getPhone())) {
            throw new EmployeePhoneAlreadyExistsException("Phone number already exists");
        }
        return employeeRepository.save(employee);
    }

    public Employee saveEmployee(Employee employee) {
        return employeeRepository.save(employee);
    }

    public Employee getEmployeeById(Long id) {
        Optional<Employee> employee = employeeRepository.findById(id);
        return employee.orElse(null);
    }

    public void deleteEmployee(Long id) {
        employeeRepository.deleteById(id);
    }

    public boolean existsById(Long id) {
        return employeeRepository.existsById(id);
    }

    public List<Employee> getAllEmployees() {
        return employeeRepository.findAll();
    }

    public long getEmployeeCount() {
        return employeeRepository.count();
    }
}
