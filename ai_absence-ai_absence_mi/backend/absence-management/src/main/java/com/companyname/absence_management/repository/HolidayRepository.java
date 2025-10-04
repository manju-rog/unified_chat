package com.companyname.absence_management.repository;

import com.companyname.absence_management.model.Holiday;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
import java.util.List;

public interface HolidayRepository extends JpaRepository<Holiday, Long> {
    List<Holiday> findByYearAndCountryCode(int year, String countryCode);
    
    @Query("SELECT h FROM Holiday h WHERE h.date BETWEEN :from AND :to AND h.countryCode = :country")
    List<Holiday> findRange(@Param("country") String country, @Param("from") LocalDate from, @Param("to") LocalDate to);
}