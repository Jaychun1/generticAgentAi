import sqlite3
import os
import pandas as pd

def init_database():
    """Initialize SQLite database with sample data"""
    
    os.makedirs("data", exist_ok=True)
    
    db_path = "data/employees.db"
    
    if os.path.exists(db_path):
        print("Database already exists")
        return db_path
    
    conn = sqlite3.connect(db_path)
    
    conn.execute('''
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        department TEXT,
        salary INTEGER,
        hire_date TEXT,
        position TEXT
    )
    ''')
    
    # Sample data
    employees_data = [
        (1, 'John Doe', 'john@example.com', 'Engineering', 85000, '2020-01-15', 'Senior Developer'),
        (2, 'Jane Smith', 'jane@example.com', 'Marketing', 72000, '2019-03-20', 'Marketing Manager'),
        (3, 'Bob Johnson', 'bob@example.com', 'Sales', 68000, '2021-07-10', 'Sales Executive'),
        (4, 'Alice Brown', 'alice@example.com', 'Engineering', 92000, '2018-11-05', 'Lead Developer'),
        (5, 'Charlie Wilson', 'charlie@example.com', 'HR', 65000, '2022-02-28', 'HR Specialist'),
        (6, 'Diana Lee', 'diana@example.com', 'Finance', 75000, '2020-09-15', 'Financial Analyst'),
        (7, 'Edward Chen', 'edward@example.com', 'Engineering', 88000, '2021-04-12', 'Software Engineer'),
        (8, 'Fiona Wang', 'fiona@example.com', 'Marketing', 70000, '2019-08-22', 'Marketing Specialist'),
        (9, 'George Kim', 'george@example.com', 'Sales', 72000, '2023-01-10', 'Sales Associate'),
        (10, 'Helen Garcia', 'helen@example.com', 'HR', 68000, '2022-06-30', 'HR Assistant')
    ]
    
    conn.executemany('INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)', employees_data)
    
    # Create departments table
    conn.execute('''
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY,
        name TEXT,
        manager_id INTEGER,
        budget INTEGER
    )
    ''')
    
    departments_data = [
        (1, 'Engineering', 1, 500000),
        (2, 'Marketing', 2, 300000),
        (3, 'Sales', 3, 400000),
        (4, 'HR', 5, 200000),
        (5, 'Finance', 6, 350000)
    ]
    
    conn.executemany('INSERT INTO departments VALUES (?, ?, ?, ?)', departments_data)
    
    # Create projects table
    conn.execute('''
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department_id INTEGER,
        status TEXT
    )
    ''')
    
    projects_data = [
        (1, 'AI Platform Development', 1, 'In Progress'),
        (2, 'Q4 Marketing Campaign', 2, 'Completed'),
        (3, 'Sales Training Program', 3, 'Planning')
    ]
    
    conn.executemany('INSERT INTO projects VALUES (?, ?, ?, ?)', projects_data)
    
    conn.commit()
    conn.close()
    
    print("Database initialized with sample data")
    return db_path

# Initialize database when module is imported
init_database()