import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, timedelta, time

# ======================================================
# DATABASE CONNECTION
# ======================================================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("medivista.db", check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_connection()
c = conn.cursor()

# ======================================================
# SCHEMA SAFE INITIALIZATION
# ======================================================

def ensure_appointments_schema():
    try:
        # Check if column exists
        c.execute("PRAGMA table_info(appointments)")
        columns = [col[1] for col in c.fetchall()]
        if "room_amount" not in columns:
            c.execute("DROP TABLE IF EXISTS appointments")
            raise Exception("Recreating table")
    except:
        c.execute("""
        CREATE TABLE appointments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT,
            doctor TEXT,
            slot TEXT,
            date TEXT,
            amount REAL DEFAULT 0,
            room TEXT DEFAULT '',
            room_amount REAL DEFAULT 0
        )
        """)
        conn.commit()

def init_db():

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        email TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS doctors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        specialist TEXT,
        nurse TEXT,
        start_time TEXT,
        end_time TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS nurses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        shift_start TEXT,
        shift_end TEXT,
        allocated_doctor TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS patients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        blood_group TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS rooms(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT UNIQUE,
        room_type TEXT,
        status TEXT
    )
    """)

    ensure_appointments_schema()

    # Default Admin
    c.execute("""
    INSERT OR IGNORE INTO users
    VALUES ('admin@admin.com',
            ?,
            'Admin',
            'Super Admin')
    """, (hashlib.sha256("Admin@123".encode()).hexdigest(),))

    conn.commit()

init_db()

# ======================================================
# UTILITIES
# ======================================================

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def generate_slots(start, end):
    slots = []
    current = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    while current < end_dt:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=20)
    return slots

# ======================================================
# UI
# ======================================================

st.set_page_config(layout="wide")

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);}
section[data-testid="stSidebar"]{background-color:#0d1117;}
div.stButton>button{
background:linear-gradient(90deg,#00c6ff,#0072ff);
border-radius:20px;color:white;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ======================================================
# SESSION
# ======================================================

if "user" not in st.session_state:
    st.session_state.user = None

# ======================================================
# LOGIN
# ======================================================

if st.session_state.user is None:

    st.title("🏥 MediVista Hospital Portal")

    mode = st.radio("Login / Register", ["Login","Register"], horizontal=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Register":
        role = st.selectbox("Role", ["Patient"])
        if st.button("Register"):
            try:
                c.execute("INSERT INTO users VALUES (?,?,?,?)",
                          (email,hash_password(password),role,email))
                conn.commit()
                st.success("Registered")
            except:
                st.warning("User already exists")

    if mode == "Login":
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE email=? AND password=?",
                      (email,hash_password(password)))
            user = c.fetchone()
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

# ======================================================
# MAIN SYSTEM
# ======================================================

else:

    role = st.session_state.user[2]
    name = st.session_state.user[3]

    st.sidebar.title("MediVista")
    st.sidebar.write(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # ==================================================
    # RECEPTIONIST BOOKING FIXED
    # ==================================================

    if role == "Receptionist":

        st.title("Book Appointment")

        doctors = pd.read_sql("SELECT * FROM doctors", conn)
        patients = pd.read_sql("SELECT * FROM patients", conn)

        if not doctors.empty and not patients.empty:

            doctor = st.selectbox("Doctor", doctors["name"])
            patient = st.selectbox("Patient", patients["name"])
            date = st.date_input("Date")
            amount = st.number_input("Appointment Payment")

            slots = generate_slots(time(8,0), time(18,0))
            slot = st.selectbox("20-min Slot", slots)

            if st.button("Confirm Booking"):

                c.execute("""
                INSERT INTO appointments
                (patient,doctor,slot,date,amount,room,room_amount)
                VALUES (?,?,?,?,?,?,?)
                """,(patient,doctor,slot,str(date),amount,"",0))

                conn.commit()
                st.success("Appointment Booked Successfully")
