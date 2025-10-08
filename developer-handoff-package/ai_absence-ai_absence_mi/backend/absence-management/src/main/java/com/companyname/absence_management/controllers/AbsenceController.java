package com.companyname.absence_management.controllers;

import com.companyname.absence_management.response.ApiResponse;
import com.companyname.absence_management.dto.AbsenceBulkUpdateRequest;
import com.companyname.absence_management.model.AbsenceRecord;
import com.companyname.absence_management.model.Holiday;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import com.companyname.absence_management.repository.EmployeeRepository;
import com.companyname.absence_management.services.HolidayService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import com.companyname.absence_management.services.AbsenceService;

import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/absences")
@CrossOrigin(origins = "*")
public class AbsenceController {

    private final AbsenceService absenceService;
    private final AbsenceRecordRepository absenceRepo;
    private final EmployeeRepository employeeRepo;
    private final HolidayService holidayService;

    @Autowired
    public AbsenceController(AbsenceService absenceService, 
                           AbsenceRecordRepository absenceRepo,
                           EmployeeRepository employeeRepo,
                           HolidayService holidayService) {
        this.absenceService = absenceService;
        this.absenceRepo = absenceRepo;
        this.employeeRepo = employeeRepo;
        this.holidayService = holidayService;
    }

    @PutMapping("/bulk-update")
    public ResponseEntity<ApiResponse> bulkUpdate(@RequestBody AbsenceBulkUpdateRequest request) {
        absenceService.bulkUpdateAbsences(request.getChanges());
        return ResponseEntity.ok(new ApiResponse(true, "Absences updated successfully", null));
    }

    @GetMapping("/calendar")
    public Map<String,Object> calendar(@RequestParam String from,
                                       @RequestParam String to,
                                       @RequestParam(required=false) String department,
                                       @RequestParam(defaultValue="IN") String country) {
        LocalDate start = LocalDate.parse(from);
        LocalDate end = LocalDate.parse(to);
        
        // Get total employees count (filtered by department if specified)
        int totalEmployees;
        if (department == null || department.isBlank()) {
            totalEmployees = (int) employeeRepo.count();
        } else {
            totalEmployees = employeeRepo.findAll().stream()
                .filter(e -> department.equalsIgnoreCase(e.getDepartment()))
                .toArray().length;
        }

        // Preload holidays for range
        List<Holiday> holidays = holidayService.listInRange(country, start, end);
        Map<LocalDate, Holiday> holByDate = holidays.stream()
            .collect(Collectors.toMap(Holiday::getDate, h->h, (a,b)->a));

        List<Map<String,Object>> days = new ArrayList<>();
        for (LocalDate d = start; !d.isAfter(end); d = d.plusDays(1)) {
            // fetch all records for this date
            List<AbsenceRecord> records = absenceRepo.findByAbsenceDate(d);
            if (department != null && !department.isBlank()) {
                records = records.stream()
                    .filter(r -> r.getEmployee() != null && 
                            department.equalsIgnoreCase(r.getEmployee().getDepartment()))
                    .collect(Collectors.toList());
            }
            
            long a = records.stream().filter(r -> r.getAbsenceType() == AbsenceRecord.AbsenceType.A).count();
            long v = records.stream().filter(r -> r.getAbsenceType() == AbsenceRecord.AbsenceType.V).count();
            long present = Math.max(0, totalEmployees - (a + v)); // P = default (no record)

            Map<String,Object> one = new HashMap<>();
            one.put("date", d.toString());
            one.put("A", a);
            one.put("V", v);
            one.put("P", present);

            Holiday h = holByDate.get(d);
            if (h != null) {
                Map<String,Object> hm = new HashMap<>();
                hm.put("name", h.getName());
                hm.put("countryCode", h.getCountryCode());
                one.put("holiday", hm);
            } else {
                one.put("holiday", null);
            }

            days.add(one);
        }

        Map<String,Object> out = new HashMap<>();
        out.put("from", start.toString());
        out.put("to", end.toString());
        out.put("days", days);
        out.put("department", department == null ? "" : department);
        return out;
    }

    @GetMapping("/calendar/day-details")
    public Map<String,Object> getDayDetails(@RequestParam String date,
                                          @RequestParam(required=false) String department,
                                          @RequestParam(defaultValue="IN") String country) {
        LocalDate targetDate = LocalDate.parse(date);
        System.out.println("Getting day details for date: " + date + ", department: " + department);
        
        // Get all employees (filtered by department if specified)
        List<com.companyname.absence_management.model.Employee> allEmployees = employeeRepo.findAll();
        System.out.println("Found " + allEmployees.size() + " total employees");
        
        if (department != null && !department.isBlank()) {
            allEmployees = allEmployees.stream()
                .filter(e -> department.equalsIgnoreCase(e.getDepartment()))
                .collect(Collectors.toList());
            System.out.println("Filtered to " + allEmployees.size() + " employees for department: " + department);
        }
        
        // Get absence records for this date
        List<AbsenceRecord> records = absenceRepo.findByAbsenceDate(targetDate);
        System.out.println("Found " + records.size() + " absence records for date: " + targetDate);
        
        if (department != null && !department.isBlank()) {
            records = records.stream()
                .filter(r -> r.getEmployee() != null && 
                        department.equalsIgnoreCase(r.getEmployee().getDepartment()))
                .collect(Collectors.toList());
            System.out.println("Filtered to " + records.size() + " absence records for department: " + department);
        }
        
        // Get holiday information
        List<Holiday> holidays = holidayService.listInRange(country, targetDate, targetDate);
        Holiday holiday = holidays.isEmpty() ? null : holidays.get(0);
        
        // Categorize employees
        Map<String, List<Map<String,Object>>> employeesByStatus = new HashMap<>();
        employeesByStatus.put("A", new ArrayList<>());
        employeesByStatus.put("V", new ArrayList<>());
        employeesByStatus.put("P", new ArrayList<>());
        
        // Create a map of employee records for quick lookup
        Map<Long, AbsenceRecord> recordMap = new HashMap<>();
        for (AbsenceRecord record : records) {
            if (record.getEmployee() != null) {
                recordMap.put(record.getEmployee().getId(), record);
            }
        }
        
        // Process each employee
        for (com.companyname.absence_management.model.Employee emp : allEmployees) {
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
        
        // Build response
        Map<String,Object> response = new HashMap<>();
        response.put("date", date);
        response.put("dayOfWeek", targetDate.getDayOfWeek().toString());
        response.put("employees", employeesByStatus);
        
        // Add holiday info if exists
        if (holiday != null) {
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
        
        System.out.println("Final stats - Total: " + allEmployees.size() + 
                          ", A: " + employeesByStatus.get("A").size() + 
                          ", V: " + employeesByStatus.get("V").size() + 
                          ", P: " + employeesByStatus.get("P").size());
        
        // Department breakdown
        if (department == null || department.isBlank()) {
            Map<String, Map<String,Integer>> deptBreakdown = new HashMap<>();
            for (com.companyname.absence_management.model.Employee emp : allEmployees) {
                String dept = emp.getDepartment() != null ? emp.getDepartment() : "Unknown";
                deptBreakdown.putIfAbsent(dept, new HashMap<>());
                
                AbsenceRecord record = recordMap.get(emp.getId());
                String status = record != null ? record.getAbsenceType().toString() : "P";
                
                Map<String,Integer> deptStats = deptBreakdown.get(dept);
                deptStats.put(status, deptStats.getOrDefault(status, 0) + 1);
            }
            stats.put("departmentBreakdown", deptBreakdown);
        }
        
        response.put("statistics", stats);
        response.put("department", department == null ? "" : department);
        
        return response;
    }
}

