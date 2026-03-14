import os
from utils.db import get_db_connection, execute_query

conn = get_db_connection()

is_postgres = hasattr(conn, "cursor") and conn.__class__.__module__.startswith("psycopg2")

try:
    if is_postgres:
        execute_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone TEXT
            )
            """,
        )
        execute_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                student_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                copies INTEGER NOT NULL,
                pages INTEGER,
                print_type TEXT NOT NULL,
                status TEXT DEFAULT 'Inbox',
                seen INTEGER DEFAULT 0,
                order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
    else:
        execute_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone TEXT
            )
            """,
        )
        execute_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                copies INTEGER NOT NULL,
                pages INTEGER,
                print_type TEXT NOT NULL,
                status TEXT DEFAULT 'Inbox',
                seen INTEGER DEFAULT 0,
                order_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
    conn.commit()
finally:
    conn.close()

print("Database initialized and tables created: students, orders")

