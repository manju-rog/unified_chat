-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    department VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    manager VARCHAR(255),
    join_date DATE,
    employee_id VARCHAR(50) UNIQUE,
    system_name VARCHAR(255),
    system_ip VARCHAR(45),
    created_at DATE,
    updated_at DATE
);

-- Create absence_records table
CREATE TABLE IF NOT EXISTS absence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    absence_date DATE NOT NULL,
    absence_type VARCHAR(20) NOT NULL CHECK (absence_type IN ('P', 'A', 'V')),
    reason VARCHAR(500),
    approved_by VARCHAR(255),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    notes VARCHAR(1000),
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_employees_employee_id ON employees(employee_id);
CREATE INDEX IF NOT EXISTS idx_absence_records_employee_id ON absence_records(employee_id);
CREATE INDEX IF NOT EXISTS idx_absence_records_date ON absence_records(absence_date);