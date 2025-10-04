package com.companyname.absence_management.service;

import com.companyname.absence_management.model.Holiday;
import com.companyname.absence_management.services.HolidayService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.time.LocalDate;

@Component
public class HolidayDataSeeder {
    
    private final HolidayService holidayService;
    
    @Autowired
    public HolidayDataSeeder(HolidayService holidayService) {
        this.holidayService = holidayService;
    }
    
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
        
        // Add some 2024 holidays for testing
        if (holidayService.listByYear("IN", 2024).isEmpty()) {
            createHoliday("2024-01-26", "Republic Day", "IN");
            createHoliday("2024-03-25", "Holi", "IN");
            createHoliday("2024-08-15", "Independence Day", "IN");
            createHoliday("2024-10-02", "Gandhi Jayanti", "IN");
            createHoliday("2024-11-01", "Diwali", "IN");
            createHoliday("2024-12-25", "Christmas Day", "IN");
        }
    }
    
    private void createHoliday(String dateStr, String name, String countryCode) {
        Holiday h = new Holiday();
        h.setDate(LocalDate.parse(dateStr));
        h.setName(name);
        h.setCountryCode(countryCode);
        holidayService.upsert(h);
    }
}