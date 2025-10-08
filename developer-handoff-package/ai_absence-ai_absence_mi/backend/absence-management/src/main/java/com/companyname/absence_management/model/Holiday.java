package com.companyname.absence_management.model;

import jakarta.persistence.*;
import java.time.LocalDate;

@Entity
@Table(name = "holidays", indexes = {
    @Index(name="idx_holiday_date", columnList = "date"),
    @Index(name="idx_holiday_year_country", columnList = "year,country_code")
})
public class Holiday {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable=false)
    private LocalDate date;

    @Column(nullable=false)
    private Integer year;

    @Column(name="name", nullable=false, length=160)
    private String name;

    @Column(name="country_code", nullable=false, length=8)
    private String countryCode;

    @Column(length=32)
    private String region; // optional

    // Constructors
    public Holiday() {}

    public Holiday(LocalDate date, String name, String countryCode) {
        this.date = date;
        this.year = date.getYear();
        this.name = name;
        this.countryCode = countryCode;
    }

    // Getters and setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public LocalDate getDate() {
        return date;
    }

    public void setDate(LocalDate date) {
        this.date = date;
        if (date != null) {
            this.year = date.getYear();
        }
    }

    public Integer getYear() {
        return year;
    }

    public void setYear(Integer year) {
        this.year = year;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getCountryCode() {
        return countryCode;
    }

    public void setCountryCode(String countryCode) {
        this.countryCode = countryCode;
    }

    public String getRegion() {
        return region;
    }

    public void setRegion(String region) {
        this.region = region;
    }
}