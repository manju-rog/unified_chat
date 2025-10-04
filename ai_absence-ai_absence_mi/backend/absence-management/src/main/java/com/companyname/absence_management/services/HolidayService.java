package com.companyname.absence_management.services;

import com.companyname.absence_management.model.Holiday;
import com.companyname.absence_management.repository.HolidayRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class HolidayService {
    private final HolidayRepository repo;
    
    public HolidayService(HolidayRepository repo) {
        this.repo = repo;
    }

    public List<Holiday> listByYear(String country, int year) {
        return repo.findByYearAndCountryCode(year, country);
    }

    public List<Holiday> listInRange(String country, LocalDate from, LocalDate to) {
        return repo.findRange(country, from, to);
    }

    public void upsert(Holiday h) {
        repo.save(h);
    }
}