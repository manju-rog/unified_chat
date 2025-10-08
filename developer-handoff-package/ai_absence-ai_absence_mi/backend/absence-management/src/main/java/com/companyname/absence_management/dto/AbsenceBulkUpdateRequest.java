package com.companyname.absence_management.dto;

import lombok.Data;

import java.util.List;

@Data
public class AbsenceBulkUpdateRequest {
    private List<AbsenceChangeDTO> changes;
}
