-- PostgreSQL schema for Neon

-- Drop tables if they already exist (development only)
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS students;

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15)
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    copies INT NOT NULL,
    pages INT,
    print_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'Inbox',
    seen INT DEFAULT 0,
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);