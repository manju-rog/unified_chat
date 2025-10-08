package com.companyname.absence_management.exception;

public class EmployeeEmailAlreadyExistsException extends RuntimeException {
    public EmployeeEmailAlreadyExistsException(String message) {
        super(message);
    }
}