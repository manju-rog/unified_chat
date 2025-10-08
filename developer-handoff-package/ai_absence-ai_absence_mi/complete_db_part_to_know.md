# Complete Database Architecture Guide - Absence Management System

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Database Configuration](#database-configuration)
3. [Database Models (Entities)](#database-models-entities)
4. [Repository Layer](#repository-layer)
5. [Service Layer](#service-layer)
6. [Controller Layer](#controller-layer)
7. [Data Initialization](#data-initialization)
8. [Frontend Database Integration](#frontend-database-integration)
9. [Complete Data Flow](#complete-data-flow)
10. [Database Schema](#database-schema)

---

## 🏗️ Project Overview

This is a **Spring Boot** backend with **React** frontend application for managing employee absences. The system uses:
- **SQLite Database** (file-based, persistent)
- **Spring Data JPA** (for database operations)
- **Hibernate** (ORM framework)
- **REST APIs** (for frontend-backend communication)

### Project Structure
```
backend/absence-management/
├── src/main/java/com/companyname/absence_management/
│   ├── model/           # Database entities (tables)
│   ├── repository/      # Database access layer
│   ├── services/        # Business logic layer
│   ├── controllers/     # REST API endpoints
│   └── config/          # Configuration files
├── src/main/resources/
│   ├── application.properties      # Main config
│   ├── application-sqlite.properties  # Database config
│   ├── schema.sql      # Database table structure
│   └── data.sql        # Initial data
└── abscent.db          # SQLite database file

frontend/src/
├── services/
│   ├── api.js          # API calls to backend
│   └── dataSync.js     # Data synchronization
└── components/         # React components
```

---

## ⚙️ Database Configuration

### 1. Main Configuration (`application.properties`)
```properties
# Activates SQLite profile
spring.profiles.active=sqlite
server.port=8080

# AI Configuration (not database related)
ai.gemini.api-key=${GEMINI_API_KEY:your-api-key-here}
```

### 2. SQLite Database Configuration (`application-sqlite.properties`)
```properties
# 🗄️ DATABASE CONNECTION
spring.datasource.url=jdbc:sqlite:./abscent.db    # Database file location
spring.datasource.driver-class-name=org.sqlite.JDBC
# SQLite doesn't need username/password

# 🔧 JPA/HIBERNATE SETTINGS
spring.jpa.hibernate.ddl-auto=update              # Auto-create/update tables
spring.jpa.show-sql=true                          # Show SQL queries in logs
spring.jpa.properties.hibernate.dialect=org.hibernate.community.dialect.SQLiteDialect
spring.jpa.properties.hibernate.format_sql=true  # Format SQL for readability
spring.jpa.defer-datasource-initialization=false
spring.sql.init.mode=never                       # Don't run schema.sql automatically
```

### 3. Dependencies (`pom.xml`)
```xml
<!-- Spring Data JPA for database operations -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>

<!-- SQLite database driver -->
<dependency>
    <groupId>org.xerial</groupId>
    <artifactId>sqlite-jdbc</artifactId>
    <version>3.44.1.0</version>
</dependency>

<!-- Hibernate SQLite dialect -->
<dependency>
    <groupId>org.hibernate.orm</groupId>
    <artifactId>hibernate-community-dialects</artifactId>
    <version>6.4.4.Final</version>
</dependency>
```

---

## 🗃️ Database Models (Entities)

### 1. Employee Entity (`Employee.java`)
**Purpose**: Stores employee information
**Table**: `employees`

```java
@Entity
@Table(name = "employees")
public class Employee {
    // 🆔 PRIMARY KEY
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 👤 BASIC INFO
    @NotBlank(message = "Employee name is required")
    @Column(nullable = false)
    private String name;

    @Email(message = "Please provide a valid email")
    @Column(nullable = false, unique = true)  // Must be unique
    private String email;

    @Column(name = "phone_number")
    private String phone;

    // 🏢 WORK INFO
    @Column(nullable = false)
    private String department;
    
    @Column(nullable = false)
    private String role;
    
    @Column(nullable = false)
    private String location;
    
    private String manager;
    
    @Column(name = "join_date")
    private LocalDate joinDate;
    
    @Column(name = "employee_id", unique = true)  // Must be unique
    private String employeeId;

    // 💻 SYSTEM INFO
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
}
```

**Key Features**:
- Auto-generated ID
- Unique constraints on email and employeeId
- One-to-many relationship with AbsenceRecord
- Automatic timestamp management
- Validation annotations

### 2. AbsenceRecord Entity (`AbsenceRecord.java`)
**Purpose**: Stores employee absence/presence records
**Table**: `absence_records`

```java
@Entity
@Table(name = "absence_records")
public class AbsenceRecord {
    // 🆔 PRIMARY KEY
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 🔗 RELATIONSHIP: Links to Employee table
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "employee_id", nullable = false)
    @NotNull(message = "Employee is required")
    @JsonBackReference
    private Employee employee;

    // 📅 ABSENCE INFORMATION
    @Column(name = "absence_date", nullable = false)
    @NotNull(message = "Absence date is required")
    private LocalDate absenceDate;

    @Column(name = "absence_type", nullable = false)
    @NotNull(message = "Absence type is required")
    @Enumerated(EnumType.STRING)
    private AbsenceType absenceType;

    // 📝 ADDITIONAL DETAILS
    @Column(length = 500)
    private String reason;
    
    @Column(name = "approved_by")
    private String approvedBy;
    
    @Enumerated(EnumType.STRING)
    private AbsenceStatus status = AbsenceStatus.PENDING;
    
    @Column(length = 1000)
    private String notes;

    // 📊 AUDIT FIELDS
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // 🏷️ ABSENCE TYPE ENUM - Only three types
    public enum AbsenceType {
        P("Present"),    // 🟢 Present
        A("Absent"),     // 🔴 Absent
        V("Vacation");   // 🔵 Vacation
    }

    // 📋 ABSENCE STATUS ENUM - Approval workflow
    public enum AbsenceStatus {
        PENDING,    // ⏳ Waiting for approval
        APPROVED,   // ✅ Approved by manager
        REJECTED    // ❌ Rejected by manager
    }
}
```

**Key Features**:
- Many-to-one relationship with Employee
- Enum types for absence type and status
- Automatic timestamp management
- Foreign key constraint to employees table

### 3. Holiday Entity (`Holiday.java`)
**Purpose**: Stores public holidays
**Table**: `holidays`

```java
@Entity
@Table(name = "holidays", indexes = {
    @Index(name="idx_holiday_date", columnList = "date"),
    @Index(name="idx_holiday_year_country", columnList = "year,country_code")
})
public class Holiday {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable=false)
    private LocalDate date;

    @Column(nullable=false)
    private Integer year;

    @Column(name="name", nullable=false, length=160)
    private String name;

    @Column(name="country_code", nullable=false, length=8)
    private String countryCode;

    @Column(length=32)
    private String region; // optional
}
```

**Key Features**:
- Database indexes for performance
- Country-specific holidays
- Year-based organization

---

## 🗂️ Repository Layer

Repositories handle direct database access using Spring Data JPA.

### 1. EmployeeRepository (`EmployeeRepository.java`)
```java
public interface EmployeeRepository extends JpaRepository<Employee, Long> {
    // 🔍 EXISTENCE CHECKS
    boolean existsByEmail(String email);
    boolean existsByPhone(String phone);
    boolean existsByEmployeeId(String employeeId);
    
    // 🔎 FIND METHODS
    Optional<Employee> findByEmployeeId(String employeeId);
    List<Employee> findByNameContainingIgnoreCase(String name);
    
    // 🔍 CUSTOM QUERY
    @Query("SELECT e FROM Employee e WHERE LOWER(e.name) LIKE LOWER(CONCAT('%', :name, '%'))")
    List<Employee> findByNameIgnoreCase(@Param("name") String name);
}
```

**Inherited Methods from JpaRepository**:
- `findAll()` - Get all employees
- `findById(Long id)` - Get employee by ID
- `save(Employee employee)` - Save/update employee
- `deleteById(Long id)` - Delete employee
- `count()` - Count total employees

### 2. AbsenceRecordRepository (`AbsenceRecordRepository.java`)
```java
public interface AbsenceRecordRepository extends JpaRepository<AbsenceRecord, Long> {
    
    // 🔍 FIND BY EMPLOYEE AND DATE
    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.employee.id = :employeeId AND ar.absenceDate = :absenceDate")
    Optional<AbsenceRecord> findByEmployeeIdAndAbsenceDate(@Param("employeeId") Long employeeId, @Param("absenceDate") LocalDate absenceDate);
    
    // 📅 FIND BY DATE
    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.absenceDate = :absenceDate")
    List<AbsenceRecord> findByAbsenceDate(@Param("absenceDate") LocalDate absenceDate);
    
    // 📊 FIND BY DATE RANGE
    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.absenceDate BETWEEN :startDate AND :endDate")
    List<AbsenceRecord> findByAbsenceDateBetween(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate);
    
    // 🎯 FIND BY DATE AND TYPES
    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.absenceDate BETWEEN :startDate AND :endDate AND ar.absenceType IN :absenceTypes")
    List<AbsenceRecord> findByAbsenceDateBetweenAndAbsenceTypeIn(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate, @Param("absenceTypes") List<AbsenceRecord.AbsenceType> absenceTypes);
}
```

**Key Features**:
- Custom JPQL queries
- JOIN FETCH for performance (avoids N+1 problem)
- Date range queries
- Type filtering

### 3. HolidayRepository (`HolidayRepository.java`)
```java
public interface HolidayRepository extends JpaRepository<Holiday, Long> {
    // 🌍 FIND BY YEAR AND COUNTRY
    List<Holiday> findByYearAndCountryCode(int year, String countryCode);
    
    // 📅 FIND BY DATE RANGE
    @Query("SELECT h FROM Holiday h WHERE h.date BETWEEN :from AND :to AND h.countryCode = :country")
    List<Holiday> findRange(@Param("country") String country, @Param("from") LocalDate from, @Param("to") LocalDate to);
}
```

---

## 🔧 Service Layer

Services contain business logic and coordinate between controllers and repositories.

### 1. EmployeeService (`EmployeeService.java`)
```java
@Service
public class EmployeeService {
    @Autowired
    private EmployeeRepository employeeRepository;

    // ➕ ADD EMPLOYEE WITH VALIDATION
    public Employee addEmployee(Employee employee) {
        // Check for duplicates
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

    // 💾 BASIC CRUD OPERATIONS
    public Employee saveEmployee(Employee employee) {
        return employeeRepository.save(employee);
    }

    public Employee getEmployeeById(Long id) {
        return employeeRepository.findById(id).orElse(null);
    }

    public void deleteEmployee(Long id) {
        employeeRepository.deleteById(id);
    }

    public List<Employee> getAllEmployees() {
        return employeeRepository.findAll();
    }

    public long getEmployeeCount() {
        return employeeRepository.count();
    }
}
```

### 2. AbsenceService (`AbsenceService.java`)
```java
@Service
public class AbsenceService {
    private final EmployeeRepository employeeRepository;
    private final AbsenceRecordRepository absenceRecordRepository;

    // 📊 BULK UPDATE ABSENCES
    @Transactional
    public void bulkUpdateAbsences(List<AbsenceChangeDTO> changes) {
        for (AbsenceChangeDTO dto : changes) {
            // Validate required fields
            if (dto.getEmployeeId() == null || dto.getAbsenceDate() == null || dto.getAbsenceType() == null) {
                throw new InvalidAbsenceDataException("Missing required fields");
            }

            // Get employee
            Employee employee = employeeRepository.findById(dto.getEmployeeId())
                    .orElseThrow(() -> new EmployeeNotFoundException(dto.getEmployeeId()));

            LocalDate absenceDate = LocalDate.parse(dto.getAbsenceDate());

            // Check if record exists
            Optional<AbsenceRecord> existingRecordOpt =
                    absenceRecordRepository.findByEmployeeIdAndAbsenceDate(employee.getId(), absenceDate);

            if ("P".equalsIgnoreCase(dto.getAbsenceType())) {
                // "P" (Present) means delete any existing absence record
                existingRecordOpt.ifPresent(absenceRecordRepository::delete);
            } else {
                // Create or update absence record
                AbsenceRecord record = existingRecordOpt.orElse(new AbsenceRecord());
                record.setEmployee(employee);
                record.setAbsenceDate(absenceDate);
                
                // Convert string to enum
                AbsenceRecord.AbsenceType absenceType = AbsenceRecord.AbsenceType.valueOf(dto.getAbsenceType().toUpperCase());
                record.setAbsenceType(absenceType);
                
                record.setReason(dto.getReason() != null ? dto.getReason() : "Not specified");
                record.setStatus(AbsenceRecord.AbsenceStatus.APPROVED);
                absenceRecordRepository.save(record);
            }
        }
    }

    // 🤖 AI INTEGRATION METHOD
    @Transactional
    public void markAbsenceFromAI(Long employeeId, List<LocalDate> dates, String status, String reason) {
        Employee employee = employeeRepository.findById(employeeId)
                .orElseThrow(() -> new EmployeeNotFoundException(employeeId));

        for (LocalDate date : dates) {
            // Similar logic as bulk update but for AI chatbot
            // ... (implementation details)
        }
    }
}
```

### 3. HolidayService (`HolidayService.java`)
```java
@Service
public class HolidayService {
    private final HolidayRepository repo;

    // 📅 GET HOLIDAYS BY YEAR
    public List<Holiday> listByYear(String country, int year) {
        return repo.findByYearAndCountryCode(year, country);
    }

    // 📊 GET HOLIDAYS IN DATE RANGE
    public List<Holiday> listInRange(String country, LocalDate from, LocalDate to) {
        return repo.findRange(country, from, to);
    }

    // 💾 SAVE HOLIDAY
    public void upsert(Holiday h) {
        repo.save(h);
    }
}
```

---

## 🌐 Controller Layer

Controllers expose REST API endpoints for frontend communication.

### 1. EmployeeController (`EmployeeController.java`)
```java
@RestController
@RequestMapping("/api/employees")
@CrossOrigin(origins = "*")
public class EmployeeController {
    @Autowired
    private EmployeeService employeeService;

    // 📋 GET ALL EMPLOYEES
    @GetMapping
    public ResponseEntity<List<Employee>> getAllEmployees() {
        List<Employee> employees = employeeService.getAllEmployees();
        return ResponseEntity.ok(employees);
    }

    // 👤 GET EMPLOYEE BY ID
    @GetMapping("/{id}")
    public ResponseEntity<Employee> getEmployeeById(@PathVariable Long id) {
        Employee employee = employeeService.getEmployeeById(id);
        return employee != null ? ResponseEntity.ok(employee) : ResponseEntity.notFound().build();
    }

    // ➕ CREATE EMPLOYEE
    @PostMapping
    public ResponseEntity<Employee> createEmployee(@RequestBody Employee employee) {
        Employee savedEmployee = employeeService.saveEmployee(employee);
        return ResponseEntity.ok(savedEmployee);
    }

    // ✏️ UPDATE EMPLOYEE
    @PutMapping("/{id}")
    public ResponseEntity<Employee> updateEmployee(@PathVariable Long id, @RequestBody Employee employee) {
        employee.setId(id);
        Employee updatedEmployee = employeeService.saveEmployee(employee);
        return ResponseEntity.ok(updatedEmployee);
    }

    // 🗑️ DELETE EMPLOYEE
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteEmployee(@PathVariable Long id) {
        employeeService.deleteEmployee(id);
        return ResponseEntity.ok().build();
    }

    // 📊 GET EMPLOYEE COUNT
    @GetMapping("/count")
    public ResponseEntity<Long> getEmployeeCount() {
        long count = employeeService.getEmployeeCount();
        return ResponseEntity.ok(count);
    }
}
```

### 2. AbsenceController (`AbsenceController.java`)
```java
@RestController
@RequestMapping("/api/absences")
@CrossOrigin(origins = "*")
public class AbsenceController {
    private final AbsenceService absenceService;
    private final AbsenceRecordRepository absenceRepo;
    private final EmployeeRepository employeeRepo;
    private final HolidayService holidayService;

    // 📊 BULK UPDATE ABSENCES
    @PutMapping("/bulk-update")
    public ResponseEntity<ApiResponse> bulkUpdate(@RequestBody AbsenceBulkUpdateRequest request) {
        absenceService.bulkUpdateAbsences(request.getChanges());
        return ResponseEntity.ok(new ApiResponse(true, "Absences updated successfully", null));
    }

    // 📅 CALENDAR VIEW
    @GetMapping("/calendar")
    public Map<String,Object> calendar(@RequestParam String from,
                                       @RequestParam String to,
                                       @RequestParam(required=false) String department,
                                       @RequestParam(defaultValue="IN") String country) {
        LocalDate start = LocalDate.parse(from);
        LocalDate end = LocalDate.parse(to);
        
        // Get total employees count (filtered by department if specified)
        int totalEmployees = (int) employeeRepo.count();
        if (department != null && !department.isBlank()) {
            totalEmployees = (int) employeeRepo.findAll().stream()
                .filter(e -> department.equalsIgnoreCase(e.getDepartment()))
                .count();
        }

        // Get holidays for the range
        List<Holiday> holidays = holidayService.listInRange(country, start, end);
        Map<LocalDate, Holiday> holByDate = holidays.stream()
            .collect(Collectors.toMap(Holiday::getDate, h->h, (a,b)->a));

        // Build calendar data for each day
        List<Map<String,Object>> days = new ArrayList<>();
        for (LocalDate d = start; !d.isAfter(end); d = d.plusDays(1)) {
            // Get absence records for this date
            List<AbsenceRecord> records = absenceRepo.findByAbsenceDate(d);
            if (department != null && !department.isBlank()) {
                records = records.stream()
                    .filter(r -> r.getEmployee() != null && 
                            department.equalsIgnoreCase(r.getEmployee().getDepartment()))
                    .collect(Collectors.toList());
            }
            
            // Count by type
            long a = records.stream().filter(r -> r.getAbsenceType() == AbsenceRecord.AbsenceType.A).count();
            long v = records.stream().filter(r -> r.getAbsenceType() == AbsenceRecord.AbsenceType.V).count();
            long present = Math.max(0, totalEmployees - (a + v)); // P = default (no record)

            // Build day data
            Map<String,Object> dayData = new HashMap<>();
            dayData.put("date", d.toString());
            dayData.put("A", a);
            dayData.put("V", v);
            dayData.put("P", present);

            // Add holiday info if exists
            Holiday h = holByDate.get(d);
            if (h != null) {
                Map<String,Object> holidayInfo = new HashMap<>();
                holidayInfo.put("name", h.getName());
                holidayInfo.put("countryCode", h.getCountryCode());
                dayData.put("holiday", holidayInfo);
            } else {
                dayData.put("holiday", null);
            }

            days.add(dayData);
        }

        // Build response
        Map<String,Object> response = new HashMap<>();
        response.put("from", start.toString());
        response.put("to", end.toString());
        response.put("days", days);
        response.put("department", department == null ? "" : department);
        return response;
    }

    // 📋 DAY DETAILS
    @GetMapping("/calendar/day-details")
    public Map<String,Object> getDayDetails(@RequestParam String date,
                                          @RequestParam(required=false) String department,
                                          @RequestParam(defaultValue="IN") String country) {
        LocalDate targetDate = LocalDate.parse(date);
        
        // Get all employees (filtered by department if specified)
        List<Employee> allEmployees = employeeRepo.findAll();
        if (department != null && !department.isBlank()) {
            allEmployees = allEmployees.stream()
                .filter(e -> department.equalsIgnoreCase(e.getDepartment()))
                .collect(Collectors.toList());
        }
        
        // Get absence records for this date
        List<AbsenceRecord> records = absenceRepo.findByAbsenceDate(targetDate);
        if (department != null && !department.isBlank()) {
            records = records.stream()
                .filter(r -> r.getEmployee() != null && 
                        department.equalsIgnoreCase(r.getEmployee().getDepartment()))
                .collect(Collectors.toList());
        }
        
        // Categorize employees by status
        Map<String, List<Map<String,Object>>> employeesByStatus = new HashMap<>();
        employeesByStatus.put("A", new ArrayList<>());
        employeesByStatus.put("V", new ArrayList<>());
        employeesByStatus.put("P", new ArrayList<>());
        
        // Create lookup map for quick access
        Map<Long, AbsenceRecord> recordMap = new HashMap<>();
        for (AbsenceRecord record : records) {
            if (record.getEmployee() != null) {
                recordMap.put(record.getEmployee().getId(), record);
            }
        }
        
        // Process each employee
        for (Employee emp : allEmployees) {
            AbsenceRecord record = recordMap.get(emp.getId());
            String status = record != null ? record.getAbsenceType().toString() : "P";
            
            Map<String,Object> empInfo = new HashMap<>();
            empInfo.put("id", emp.getId());
            empInfo.put("name", emp.getName());
            empInfo.put("email", emp.getEmail());
            empInfo.put("department", emp.getDepartment());
            empInfo.put("reason", record != null ? record.getReason() : null);
            
            employeesByStatus.get(status).add(empInfo);
        }
        
        // Build response with statistics
        Map<String,Object> response = new HashMap<>();
        response.put("date", date);
        response.put("dayOfWeek", targetDate.getDayOfWeek().toString());
        response.put("employees", employeesByStatus);
        
        // Add holiday info
        List<Holiday> holidays = holidayService.listInRange(country, targetDate, targetDate);
        if (!holidays.isEmpty()) {
            Holiday holiday = holidays.get(0);
            Map<String,Object> holidayInfo = new HashMap<>();
            holidayInfo.put("name", holiday.getName());
            holidayInfo.put("countryCode", holiday.getCountryCode());
            holidayInfo.put("region", holiday.getRegion());
            response.put("holiday", holidayInfo);
        } else {
            response.put("holiday", null);
        }
        
        // Add statistics
        Map<String,Object> stats = new HashMap<>();
        stats.put("totalEmployees", allEmployees.size());
        stats.put("absent", employeesByStatus.get("A").size());
        stats.put("vacation", employeesByStatus.get("V").size());
        stats.put("present", employeesByStatus.get("P").size());
        response.put("statistics", stats);
        
        return response;
    }
}
```

### 3. HolidayController (`HolidayController.java`)
```java
@RestController
@RequestMapping("/api/holidays")
@CrossOrigin(origins="*")
public class HolidayController {
    private final HolidayService service;

    // 📅 GET HOLIDAYS BY YEAR
    @GetMapping
    public List<Map<String,Object>> list(@RequestParam int year, @RequestParam(defaultValue = "IN") String country) {
        var items = service.listByYear(country, year);
        List<Map<String,Object>> out = new ArrayList<>();
        for (Holiday h: items) {
            Map<String,Object> m = new HashMap<>();
            m.put("date", h.getDate().toString());
            m.put("name", h.getName());
            m.put("countryCode", h.getCountryCode());
            m.put("region", h.getRegion());
            out.add(m);
        }
        return out;
    }
}
```

---

## 🌱 Data Initialization

### 1. DataInitializationService (`DataInitializationService.java`)
**Purpose**: Automatically populate database with initial employee data

```java
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
}
```

### 2. HolidayDataSeeder (`HolidayDataSeeder.java`)
**Purpose**: Automatically populate database with holiday data

```java
@Component
public class HolidayDataSeeder {
    private final HolidayService holidayService;
    
    @PostConstruct
    public void seedHolidays() {
        // Only seed if no holidays exist for 2025
        if (holidayService.listByYear("IN", 2025).isEmpty()) {
            seedIndianHolidays2025();
        }
    }
    
    private void seedIndianHolidays2025() {
        createHoliday("2025-01-26", "Republic Day", "IN");
        createHoliday("2025-03-14", "Holi", "IN");
        createHoliday("2025-08-15", "Independence Day", "IN");
        createHoliday("2025-10-02", "Gandhi Jayanti", "IN");
        createHoliday("2025-10-20", "Diwali", "IN");
        createHoliday("2025-12-25", "Christmas Day", "IN");
    }
}
```

---

## 🌐 Frontend Database Integration

### 1. API Service (`api.js`)
**Purpose**: Handle all HTTP requests to backend APIs

```javascript
const API_BASE_URL = 'http://localhost:8080/api';

// 👥 EMPLOYEE API
export const employeeAPI = {
    getAll: () => apiRequest('/employees'),
    getById: (id) => apiRequest(`/employees/${id}`),
    create: (employeeData) => apiRequest('/employees', {
        method: 'POST',
        body: employeeData,
    }),
    update: (id, employeeData) => apiRequest(`/employees/${id}`, {
        method: 'PUT',
        body: employeeData,
    }),
    delete: (id) => apiRequest(`/employees/${id}`, {
        method: 'DELETE',
    }),
    getCount: () => apiRequest('/employees/count'),
};

// 📊 ABSENCE API
export const absenceAPI = {
    bulkUpdate: (changes) => apiRequest('/absences/bulk-update', {
        method: 'PUT',
        body: { changes },
    }),
};

// 📅 CALENDAR API
export const calendarAPI = {
    getSummary: async ({ from, to, department }) =>
        apiRequest(`/absences/calendar?from=${from}&to=${to}${department ? `&department=${encodeURIComponent(department)}` : ''}`),
    getDayDetails: async ({ date, department, country = 'IN' }) =>
        apiRequest(`/absences/calendar/day-details?date=${date}${department ? `&department=${encodeURIComponent(department)}` : ''}&country=${country}`)
};

// 🎉 HOLIDAYS API
export const holidaysAPI = {
    get: async ({ year, country = 'IN' }) =>
        apiRequest(`/holidays?year=${year}&country=${country}`)
};
```

### 2. Data Synchronization (`dataSync.js`)
**Purpose**: Real-time data synchronization between React components

```javascript
class DataSyncService {
    constructor() {
        this.listeners = new Map();
    }

    // Subscribe to data change events
    subscribe(eventType, callback) {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, new Set());
        }
        this.listeners.get(eventType).add(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.listeners.get(eventType);
            if (callbacks) {
                callbacks.delete(callback);
            }
        };
    }

    // Emit data change events
    emit(eventType, data) {
        const callbacks = this.listeners.get(eventType);
        if (callbacks) {
            callbacks.forEach(callback => {
                callback(data);
            });
        }
    }
}

// Event types
export const DATA_EVENTS = {
    ABSENCE_DATA_CHANGED: 'absence_data_changed',
    ABSENCE_DATA_SAVED: 'absence_data_saved',
    EMPLOYEE_DATA_CHANGED: 'employee_data_changed'
};
```

---

## 🔄 Complete Data Flow

### 1. Application Startup Flow
```
1. Spring Boot Application starts
   ↓
2. Database connection established (SQLite)
   ↓
3. Hibernate creates/updates tables (ddl-auto=update)
   ↓
4. DataInitializationService runs
   ↓
5. Check if employees table is empty
   ↓
6. If empty, insert initial employee data
   ↓
7. HolidayDataSeeder runs (@PostConstruct)
   ↓
8. Insert holiday data if not exists
   ↓
9. Application ready to serve requests
```

### 2. Frontend Data Request Flow
```
React Component
   ↓ (API call)
Frontend API Service (api.js)
   ↓ (HTTP request)
Spring Boot Controller
   ↓ (method call)
Service Layer
   ↓ (repository call)
Repository Interface
   ↓ (JPA/Hibernate)
SQLite Database
   ↓ (query result)
Repository → Service → Controller
   ↓ (JSON response)
Frontend API Service
   ↓ (parsed data)
React Component (state update)
```

### 3. Database Write Operation Flow
```
Frontend Form Submission
   ↓
API Service (POST/PUT request)
   ↓
Controller (validation)
   ↓
Service (business logic)
   ↓
Repository (JPA save)
   ↓
Hibernate (SQL generation)
   ↓
SQLite Database (data persistence)
   ↓
Response back to frontend
   ↓
Component state update
   ↓
UI re-render
```

### 4. Absence Management Flow
```
User selects date and employee
   ↓
Frontend sends bulk update request
   ↓
AbsenceController.bulkUpdate()
   ↓
AbsenceService.bulkUpdateAbsences()
   ↓
For each change:
   - Find employee by ID
   - Check if absence record exists
   - If "P" (Present): delete existing record
   - If "A" or "V": create/update record
   ↓
Repository saves changes
   ↓
Database updated
   ↓
Success response to frontend
   ↓
Calendar view refreshes
```

---

## 🗄️ Database Schema

### Tables Structure

#### 1. `employees` Table
```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    department VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    manager VARCHAR(255),
    join_date DATE,
    employee_id VARCHAR(50) UNIQUE,
    system_name VARCHAR(255),
    system_ip VARCHAR(45),
    created_at DATE,
    updated_at DATE
);

-- Indexes for performance
CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employees_employee_id ON employees(employee_id);
```

#### 2. `absence_records` Table
```sql
CREATE TABLE absence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    absence_date DATE NOT NULL,
    absence_type VARCHAR(20) NOT NULL CHECK (absence_type IN ('P', 'A', 'V')),
    reason VARCHAR(500),
    approved_by VARCHAR(255),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    notes VARCHAR(1000),
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Indexes for performance
CREATE INDEX idx_absence_records_employee_id ON absence_records(employee_id);
CREATE INDEX idx_absence_records_date ON absence_records(absence_date);
```

#### 3. `holidays` Table
```sql
CREATE TABLE holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    year INTEGER NOT NULL,
    name VARCHAR(160) NOT NULL,
    country_code VARCHAR(8) NOT NULL,
    region VARCHAR(32)
);

-- Indexes for performance
CREATE INDEX idx_holiday_date ON holidays(date);
CREATE INDEX idx_holiday_year_country ON holidays(year, country_code);
```

### Relationships
- **One-to-Many**: Employee → AbsenceRecord
  - One employee can have multiple absence records
  - Foreign key: `absence_records.employee_id` → `employees.id`

- **No direct relationship**: Holiday table is independent
  - Used for calendar display and business logic
  - Queried by date range and country

### Data Types and Constraints
- **Primary Keys**: Auto-incrementing integers
- **Unique Constraints**: email, employee_id
- **Check Constraints**: absence_type, status
- **Foreign Keys**: Maintain referential integrity
- **Indexes**: Optimize query performance

---

## 🎯 Key Points for Beginners

### 1. **What is the Database?**
- SQLite file (`abscent.db`) stores all data
- No separate database server needed
- Data persists between application restarts

### 2. **How Data Flows?**
- Frontend → API calls → Controllers → Services → Repositories → Database
- Database → Repositories → Services → Controllers → JSON → Frontend

### 3. **Main Components:**
- **Models**: Define database table structure
- **Repositories**: Handle database queries
- **Services**: Business logic and validation
- **Controllers**: REST API endpoints

### 4. **Key Features:**
- Automatic table creation/updates
- Data validation and constraints
- Relationship management
- Performance optimization with indexes
- Automatic timestamp management

### 5. **How to Add New Data?**
1. Create/update model class
2. Add repository methods if needed
3. Implement service logic
4. Create controller endpoints
5. Update frontend API calls

