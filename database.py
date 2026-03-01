import sqlite3

def get_connection():
    conn = sqlite3.connect("hospital.db", check_same_thread=False)
    return conn

def create_tables():
    conn = get_connection()
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # DOCTORS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS doctors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        specialist TEXT,
        nurse TEXT,
        start_time TEXT,
        end_time TEXT
    )
    """)

    # PATIENTS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS patients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        blood_group TEXT
    )
    """)

    # ROOMS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS rooms(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT,
        room_type TEXT,
        status TEXT
    )
    """)

    # APPOINTMENTS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        doctor_name TEXT,
        slot TEXT,
        date TEXT,
        amount REAL
    )
    """)

    # QUERIES TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS queries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        target TEXT,
        message TEXT
    )
    """)

    # 🔥 AUTO CREATE ADMIN
    c.execute("""
    INSERT OR IGNORE INTO users (name,email,password,role)
    VALUES ('Admin','admin@admin.com','admin123','Admin')
    """)

    conn.commit()
    conn.close()
