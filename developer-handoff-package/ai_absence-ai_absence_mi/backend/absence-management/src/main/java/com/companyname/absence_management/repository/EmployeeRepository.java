package com.companyname.absence_management.repository;

import com.companyname.absence_management.model.Employee;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface EmployeeRepository extends JpaRepository<Employee, Long> {
   boolean existsByEmail(String email);
   boolean existsByPhone(String phone);
   boolean existsByEmployeeId(String employeeId);
   
   Optional<Employee> findByEmployeeId(String employeeId);
   List<Employee> findByNameContainingIgnoreCase(String name);
   
   @Query("SELECT e FROM Employee e WHERE LOWER(e.name) LIKE LOWER(CONCAT('%', :name, '%'))")
   List<Employee> findByNameIgnoreCase(@Param("name") String name);
}
