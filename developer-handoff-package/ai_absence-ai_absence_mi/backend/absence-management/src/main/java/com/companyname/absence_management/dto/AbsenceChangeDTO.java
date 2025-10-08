package com.companyname.absence_management.dto;

import lombok.Data;

@Data
public class AbsenceChangeDTO {

    private Long employeeId;     // Employee entity's internal ID
    private String absenceDate;  // YYYY-MM-DD string
    private String absenceType;  // "P", "A", "V" etc.
    private String reason;
}

