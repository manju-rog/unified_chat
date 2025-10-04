package com.companyname.absence_management.services;

import com.companyname.absence_management.exception.EmployeeNotFoundException;
import com.companyname.absence_management.exception.InvalidAbsenceDataException;
import com.companyname.absence_management.dto.AbsenceChangeDTO;
import jakarta.transaction.Transactional;
import com.companyname.absence_management.model.AbsenceRecord;
import com.companyname.absence_management.model.Employee;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import com.companyname.absence_management.repository.EmployeeRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Service
public class AbsenceService {

    private final EmployeeRepository employeeRepository;
    private final AbsenceRecordRepository absenceRecordRepository;

    @Autowired
    public AbsenceService(EmployeeRepository employeeRepository,
                          AbsenceRecordRepository absenceRecordRepository) {
        this.employeeRepository = employeeRepository;
        this.absenceRecordRepository = absenceRecordRepository;
    }

    @Transactional
    public void bulkUpdateAbsences(List<AbsenceChangeDTO> changes) {
        for (AbsenceChangeDTO dto : changes) {
            if (dto.getEmployeeId() == null || dto.getAbsenceDate() == null || dto.getAbsenceType() == null) {
                throw new InvalidAbsenceDataException("Missing required fields in absence record");
            }

            Employee employee = employeeRepository.findById(dto.getEmployeeId())
                    .orElseThrow(() -> new EmployeeNotFoundException(dto.getEmployeeId()));

            LocalDate absenceDate = LocalDate.parse(dto.getAbsenceDate());

            Optional<AbsenceRecord> existingRecordOpt =
                    absenceRecordRepository.findByEmployeeIdAndAbsenceDate(employee.getId(), absenceDate);

            if ("P".equalsIgnoreCase(dto.getAbsenceType())) {
                // "P" (Present) means delete any existing absence record for that date
                existingRecordOpt.ifPresent(absenceRecordRepository::delete);
            } else {
                AbsenceRecord record = existingRecordOpt.orElse(new AbsenceRecord());
                record.setEmployee(employee);
                record.setAbsenceDate(absenceDate);
                
                // Convert string to enum
                AbsenceRecord.AbsenceType absenceType;
                try {
                    absenceType = AbsenceRecord.AbsenceType.valueOf(dto.getAbsenceType().toUpperCase());
                } catch (IllegalArgumentException e) {
                    throw new InvalidAbsenceDataException("Invalid absence type: " + dto.getAbsenceType());
                }
                record.setAbsenceType(absenceType);
                
                record.setReason(dto.getReason() != null ? dto.getReason() : "Not specified");
                record.setStatus(AbsenceRecord.AbsenceStatus.APPROVED); // You can adjust status logic as needed
                absenceRecordRepository.save(record);
            }
        }
    }

    /**
     * Mark absence from AI - specialized method for AI chatbot integration
     */
    @Transactional
    public void markAbsenceFromAI(Long employeeId, List<LocalDate> dates, String status, String reason) {
        Employee employee = employeeRepository.findById(employeeId)
                .orElseThrow(() -> new EmployeeNotFoundException(employeeId));

        for (LocalDate date : dates) {
            Optional<AbsenceRecord> existingRecordOpt =
                    absenceRecordRepository.findByEmployeeIdAndAbsenceDate(employeeId, date);

            if ("P".equalsIgnoreCase(status)) {
                // "P" (Present) means delete any existing absence record for that date
                existingRecordOpt.ifPresent(absenceRecordRepository::delete);
            } else {
                AbsenceRecord record = existingRecordOpt.orElse(new AbsenceRecord());
                record.setEmployee(employee);
                record.setAbsenceDate(date);
                
                // Convert string to enum
                AbsenceRecord.AbsenceType absenceType;
                try {
                    absenceType = AbsenceRecord.AbsenceType.valueOf(status.toUpperCase());
                } catch (IllegalArgumentException e) {
                    throw new InvalidAbsenceDataException("Invalid absence type: " + status);
                }
                record.setAbsenceType(absenceType);
                
                record.setReason(reason != null ? reason : "Marked by AI Assistant");
                record.setStatus(AbsenceRecord.AbsenceStatus.APPROVED);
                absenceRecordRepository.save(record);
            }
        }
    }
}

