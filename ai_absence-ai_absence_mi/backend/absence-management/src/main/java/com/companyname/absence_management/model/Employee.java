package com.companyname.absence_management.model;

import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

import java.time.LocalDate;
import java.util.List;

@Entity
@Table(name = "employees")
public class Employee {

    // 🆔 PRIMARY KEY: Unique identifier for each employee
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 👤 BASIC INFORMATION
    @NotBlank(message = "Employee name is required")
    @Column(nullable = false)
    private String name;

    @Email(message = "Please provide a valid email")
    @NotBlank(message = "Email is required")
    @Column(nullable = false, unique = true)  // 🔧 Email must be unique
    private String email;

    @Column(name = "phone_number")
    private String phone;

    // 🏢 WORK INFORMATION
    @NotBlank(message = "Department is required")
    @Column(nullable = false)
    private String department;

    @NotBlank(message = "Role is required")
    @Column(nullable = false)
    private String role;

    @NotBlank(message = "Location is required")
    @Column(nullable = false)
    private String location;

    private String manager;

    @Column(name = "join_date")
    private LocalDate joinDate;

    @Column(name = "employee_id", unique = true)  // 🔧 Employee ID must be unique
    private String employeeId;

    // 💻 SYSTEM INFORMATION
    @Column(name = "system_name")
    private String systemName;

    @Column(name = "system_ip")
    private String systemIP;

    // 🔗 RELATIONSHIP: One employee can have many absence records
    @OneToMany(mappedBy = "employee", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @JsonManagedReference
    private List<AbsenceRecord> absenceRecords;

    // 📊 AUDIT FIELDS (automatically managed)
    @Column(name = "created_at")
    private LocalDate createdAt;

    @Column(name = "updated_at")
    private LocalDate updatedAt;

    // 🔧 LIFECYCLE METHODS: Automatically set dates
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDate.now();
        updatedAt = LocalDate.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDate.now();
    }

    // 🔧 CONSTRUCTORS
    public Employee() {}

    public Employee(String name, String email, String phone, String department, String role, String location, String manager, LocalDate joinDate, String employeeId, String systemName, String systemIP) {
        this.name = name;
        this.email = email;
        this.phone = phone;
        this.department = department;
        this.role = role;
        this.location = location;
        this.manager = manager;
        this.joinDate = joinDate;
        this.employeeId = employeeId;
        this.systemName = systemName;
        this.systemIP = systemIP;
    }

    // 🔧 GETTERS AND SETTERS
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }

    public String getDepartment() { return department; }
    public void setDepartment(String department) { this.department = department; }

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }

    public String getLocation() { return location; }
    public void setLocation(String location) { this.location = location; }

    public String getManager() { return manager; }
    public void setManager(String manager) { this.manager = manager; }

    public LocalDate getJoinDate() { return joinDate; }
    public void setJoinDate(LocalDate joinDate) { this.joinDate = joinDate; }

    public String getEmployeeId() { return employeeId; }
    public void setEmployeeId(String employeeId) { this.employeeId = employeeId; }

    public String getSystemName() { return systemName; }
    public void setSystemName(String systemName) { this.systemName = systemName; }

    public String getSystemIP() { return systemIP; }
    public void setSystemIP(String systemIP) { this.systemIP = systemIP; }

    public List<AbsenceRecord> getAbsenceRecords() { return absenceRecords; }
    public void setAbsenceRecords(List<AbsenceRecord> absenceRecords) { this.absenceRecords = absenceRecords; }

    public LocalDate getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDate createdAt) { this.createdAt = createdAt; }

    public LocalDate getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDate updatedAt) { this.updatedAt = updatedAt; }

    // 🔧 BUILDER PATTERN (Manual implementation)
    public static EmployeeBuilder builder() {
        return new EmployeeBuilder();
    }

    public static class EmployeeBuilder {
        private String name, email, phone, department, role, location, manager, employeeId, systemName, systemIP;
        private LocalDate joinDate;

        public EmployeeBuilder name(String name) { this.name = name; return this; }
        public EmployeeBuilder email(String email) { this.email = email; return this; }
        public EmployeeBuilder phone(String phone) { this.phone = phone; return this; }
        public EmployeeBuilder department(String department) { this.department = department; return this; }
        public EmployeeBuilder role(String role) { this.role = role; return this; }
        public EmployeeBuilder location(String location) { this.location = location; return this; }
        public EmployeeBuilder manager(String manager) { this.manager = manager; return this; }
        public EmployeeBuilder joinDate(LocalDate joinDate) { this.joinDate = joinDate; return this; }
        public EmployeeBuilder employeeId(String employeeId) { this.employeeId = employeeId; return this; }
        public EmployeeBuilder systemName(String systemName) { this.systemName = systemName; return this; }
        public EmployeeBuilder systemIP(String systemIP) { this.systemIP = systemIP; return this; }

        public Employee build() {
            return new Employee(name, email, phone, department, role, location, manager, joinDate, employeeId, systemName, systemIP);
        }
    }
}
