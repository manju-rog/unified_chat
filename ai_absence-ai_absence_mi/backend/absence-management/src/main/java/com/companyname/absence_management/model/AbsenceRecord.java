package com.companyname.absence_management.model;

import com.fasterxml.jackson.annotation.JsonBackReference;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDate;
import java.time.LocalDateTime;

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

    // 🔧 LIFECYCLE METHODS
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    // 🏷️ ABSENCE TYPE ENUM - Only three types as requested
    public enum AbsenceType {
        P("Present"),    // 🟢 Present
        A("Absent"),     // 🔴 Absent
        V("Vacation");   // 🔵 Vacation

        private final String displayName;

        AbsenceType(String displayName) {
            this.displayName = displayName;
        }

        public String getDisplayName() {
            return displayName;
        }
    }

    // 📋 ABSENCE STATUS ENUM - Approval workflow
    public enum AbsenceStatus {
        PENDING,    // ⏳ Waiting for approval
        APPROVED,   // ✅ Approved by manager
        REJECTED    // ❌ Rejected by manager
    }

    // 🔧 CONSTRUCTORS
    public AbsenceRecord() {}

    public AbsenceRecord(Employee employee, LocalDate absenceDate, AbsenceType absenceType, String reason, AbsenceStatus status, String notes) {
        this.employee = employee;
        this.absenceDate = absenceDate;
        this.absenceType = absenceType;
        this.reason = reason;
        this.status = status;
        this.notes = notes;
    }

    // 🔧 GETTERS AND SETTERS
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Employee getEmployee() { return employee; }
    public void setEmployee(Employee employee) { this.employee = employee; }

    public LocalDate getAbsenceDate() { return absenceDate; }
    public void setAbsenceDate(LocalDate absenceDate) { this.absenceDate = absenceDate; }

    public AbsenceType getAbsenceType() { return absenceType; }
    public void setAbsenceType(AbsenceType absenceType) { this.absenceType = absenceType; }

    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }

    public String getApprovedBy() { return approvedBy; }
    public void setApprovedBy(String approvedBy) { this.approvedBy = approvedBy; }

    public AbsenceStatus getStatus() { return status; }
    public void setStatus(AbsenceStatus status) { this.status = status; }

    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }

    // 🔧 BUILDER PATTERN (Manual implementation)
    public static AbsenceRecordBuilder builder() {
        return new AbsenceRecordBuilder();
    }

    public static class AbsenceRecordBuilder {
        private Employee employee;
        private LocalDate absenceDate;
        private AbsenceType absenceType;
        private String reason;
        private AbsenceStatus status;
        private String notes;
        private String approvedBy;

        public AbsenceRecordBuilder employee(Employee employee) { this.employee = employee; return this; }
        public AbsenceRecordBuilder absenceDate(LocalDate absenceDate) { this.absenceDate = absenceDate; return this; }
        public AbsenceRecordBuilder absenceType(AbsenceType absenceType) { this.absenceType = absenceType; return this; }
        public AbsenceRecordBuilder reason(String reason) { this.reason = reason; return this; }
        public AbsenceRecordBuilder status(AbsenceStatus status) { this.status = status; return this; }
        public AbsenceRecordBuilder notes(String notes) { this.notes = notes; return this; }
        public AbsenceRecordBuilder approvedBy(String approvedBy) { this.approvedBy = approvedBy; return this; }

        public AbsenceRecord build() {
            AbsenceRecord record = new AbsenceRecord(employee, absenceDate, absenceType, reason, status, notes);
            record.setApprovedBy(approvedBy);
            return record;
        }
    }
}

