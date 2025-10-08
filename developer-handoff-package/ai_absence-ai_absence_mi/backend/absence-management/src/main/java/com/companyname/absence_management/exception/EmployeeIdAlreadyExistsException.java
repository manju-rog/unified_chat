package com.companyname.absence_management.exception;

public class EmployeeIdAlreadyExistsException extends RuntimeException {
    public EmployeeIdAlreadyExistsException(String message) {
        super(message);
    }
}