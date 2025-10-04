package com.companyname.absence_management.exception;

public class EmployeePhoneAlreadyExistsException extends RuntimeException {
    public EmployeePhoneAlreadyExistsException(String message) {
        super(message);
    }
}