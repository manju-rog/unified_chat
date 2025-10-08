package com.companyname.absence_management.repository;

import com.companyname.absence_management.model.AbsenceRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface AbsenceRecordRepository extends JpaRepository<AbsenceRecord, Long> {

    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.employee.id = :employeeId AND ar.absenceDate = :absenceDate")
    Optional<AbsenceRecord> findByEmployeeIdAndAbsenceDate(@Param("employeeId") Long employeeId, @Param("absenceDate") LocalDate absenceDate);
    
    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.absenceDate = :absenceDate")
    List<AbsenceRecord> findByAbsenceDate(@Param("absenceDate") LocalDate absenceDate);
    
    @Query("SELECT ar FROM AbsenceRecord ar WHERE ar.employee.id = :employeeId AND ar.absenceDate = :absenceDate")
    Optional<AbsenceRecord> findByEmployeeIdAndDate(@Param("employeeId") Long employeeId, @Param("absenceDate") LocalDate absenceDate);
    
    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.absenceDate = :absenceDate AND ar.absenceType IN :absenceTypes")
    List<AbsenceRecord> findByDateAndAbsenceTypes(@Param("absenceDate") LocalDate absenceDate, @Param("absenceTypes") List<AbsenceRecord.AbsenceType> absenceTypes);
    
    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.absenceDate BETWEEN :startDate AND :endDate")
    List<AbsenceRecord> findByAbsenceDateBetween(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate);
    
    @Query("SELECT ar FROM AbsenceRecord ar JOIN FETCH ar.employee WHERE ar.absenceDate BETWEEN :startDate AND :endDate AND ar.absenceType IN :absenceTypes")
    List<AbsenceRecord> findByAbsenceDateBetweenAndAbsenceTypeIn(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate, @Param("absenceTypes") List<AbsenceRecord.AbsenceType> absenceTypes);
}
