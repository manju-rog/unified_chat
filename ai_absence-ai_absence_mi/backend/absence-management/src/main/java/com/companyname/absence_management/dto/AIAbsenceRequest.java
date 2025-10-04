package com.companyname.absence_management.dto;

import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDate;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class AIAbsenceRequest {
    
    private Long employeeId;
    private List<LocalDate> dates;
    private String status; // P, A, or V
    private String reason; // Optional reason for the absence
    
    // Additional metadata for AI tracking
    private String aiRequestId;
    private String originalUserInput;
}