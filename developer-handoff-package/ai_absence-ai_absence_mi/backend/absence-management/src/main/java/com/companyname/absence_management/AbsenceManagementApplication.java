package com.companyname.absence_management;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EntityScan(basePackages = "com.companyname.absence_management.model")
@EnableScheduling
public class AbsenceManagementApplication {

	public static void main(String[] args) {
		SpringApplication.run(AbsenceManagementApplication.class, args);
	}

}
