#!/bin/bash

echo "🔍 SQLite Database Verification Script"
echo "======================================"

DB_FILE="./abscent.db"

if [ ! -f "$DB_FILE" ]; then
    echo "❌ Database file not found: $DB_FILE"
    exit 1
fi

echo "✅ Database file exists: $DB_FILE"
echo ""

echo "📊 Database Tables:"
echo "-------------------"
sqlite3 "$DB_FILE" ".tables"
echo ""

echo "🏗️  Employees Table Schema:"
echo "---------------------------"
sqlite3 "$DB_FILE" ".schema employees"
echo ""

echo "🏗️  Absence Records Table Schema:"
echo "--------------------------------"
sqlite3 "$DB_FILE" ".schema absence_records"
echo ""

echo "👥 Employee Data:"
echo "----------------"
sqlite3 "$DB_FILE" "SELECT 'Employee Count: ' || COUNT(*) FROM employees;"
echo ""
sqlite3 "$DB_FILE" "SELECT name, employee_id, department, role FROM employees ORDER BY name;"
echo ""

echo "📅 Absence Records Data:"
echo "-----------------------"
sqlite3 "$DB_FILE" "SELECT 'Absence Records Count: ' || COUNT(*) FROM absence_records;"
echo ""

if [ $(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM absence_records;") -gt 0 ]; then
    echo "Recent absence records:"
    sqlite3 "$DB_FILE" "
    SELECT 
        e.name, 
        ar.absence_date, 
        ar.absence_type, 
        ar.status 
    FROM absence_records ar 
    JOIN employees e ON ar.employee_id = e.id 
    ORDER BY ar.absence_date DESC 
    LIMIT 5;"
else
    echo "No absence records found."
fi

echo ""
echo "🔗 Database Connectivity Test:"
echo "-----------------------------"
sqlite3 "$DB_FILE" "SELECT 'Database connection successful! SQLite version: ' || sqlite_version();"

echo ""
echo "✅ Database verification complete!"