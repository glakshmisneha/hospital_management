import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
import re
from datetime import datetime, timedelta, time

# =====================================================
# DATABASE CONNECTION (SAFE VERSION)
# =====================================================

def connect_db():
    conn = sqlite3.connect("medivista_full.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")  # prevents database lock
    return conn

def init_db():
    with connect_db() as conn:
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            email TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            name TEXT
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS specialists(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
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

        c.execute("""
        CREATE TABLE IF NOT EXISTS appointments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT,
            doctor TEXT,
            slot TEXT,
            date TEXT,
            amount REAL,
            room TEXT
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS queries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            target TEXT,
            message TEXT
        )
        """)

        # SAFE ADMIN CREATION
        c.execute("""
        INSERT OR IGNORE INTO users
        VALUES ('admin@admin.com',
                ?,
                'Admin',
                'Super Admin')
        """, (hashlib.sha256("Admin@123".encode()).hexdigest(),))

init_db()

# =====================================================
# UTILITIES
# =====================================================

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def valid_email(email, role):
    if role == "Patient":
        return email.endswith("@gmail.com")
    if role == "Admin":
        return email.endswith("@admin.com")
    if role in ["Doctor","Receptionist","Staff"]:
        return email.endswith("@hospitalstaff.com")
    return False

def generate_slots(start, end):
    slots = []
    current = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    while current < end_dt:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=20)
    return slots

# =====================================================
# UI THEME
# =====================================================

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

# =====================================================
# SESSION
# =====================================================

if "user" not in st.session_state:
    st.session_state.user = None

# =====================================================
# LOGIN / REGISTER
# =====================================================

if st.session_state.user is None:

    st.title("🏥 MediVista Administrative Portal")

    option = st.radio("Select", ["Login","Register"], horizontal=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if option == "Register":
        role = st.selectbox("Role", ["Patient"])

        if st.button("Register"):
            if not valid_email(email, role):
                st.error("Invalid email format for role")
            else:
                try:
                    with connect_db() as conn:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?)",
                                     (email, hash_password(password), role, email))
                    st.success("Registered Successfully")
                except sqlite3.IntegrityError:
                    st.warning("User already exists")

    if option == "Login":
        if st.button("Login"):
            with connect_db() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE email=? AND password=?",
                          (email, hash_password(password)))
                user = c.fetchone()
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")

# =====================================================
# MAIN APP
# =====================================================

else:

    role = st.session_state.user[2]
    name = st.session_state.user[3]

    st.sidebar.title("MediVista Admin")
    st.sidebar.write(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # ================= ADMIN =================

    if role == "Admin":

        page = st.sidebar.radio("Navigation",
            ["Dashboard","Staff Registration"])

        if page == "Dashboard":
            st.title("Hospital Analytics Dashboard")

            with connect_db() as conn:
                df_appointments = pd.read_sql("SELECT * FROM appointments", conn)
                df_patients = pd.read_sql("SELECT * FROM patients", conn)
                df_doctors = pd.read_sql("SELECT * FROM doctors", conn)

            total_revenue = df_appointments["amount"].sum() if not df_appointments.empty else 0

            col1,col2,col3,col4 = st.columns(4)
            col1.metric("Total Revenue", f"₹ {total_revenue}")
            col2.metric("Total Patients", len(df_patients))
            col3.metric("Total Doctors", len(df_doctors))
            col4.metric("Total Visits", len(df_appointments))

            if not df_appointments.empty:
                rev_chart = df_appointments.groupby("date")["amount"].sum().reset_index()
                fig = px.bar(rev_chart, x="date", y="amount")
                st.plotly_chart(fig, use_container_width=True)

        elif page == "Staff Registration":

            st.title("Register Hospital Staff")

            sname = st.text_input("Name")
            semail = st.text_input("Email (@hospitalstaff.com)")
            srole = st.selectbox("Role",["Receptionist","Staff"])

            if st.button("Register Staff"):
                if not valid_email(semail, srole):
                    st.error("Invalid staff email format")
                else:
                    try:
                        with connect_db() as conn:
                            conn.execute("INSERT INTO users VALUES (?,?,?,?)",
                                         (semail,
                                          hash_password("Staff@123"),
                                          srole,
                                          sname))
                        st.success("Staff Registered (Password: Staff@123)")
                    except sqlite3.IntegrityError:
                        st.warning("Staff already registered")

    # ================= DOCTOR =================

    elif role == "Doctor":
        st.title("Doctor Dashboard")

        with connect_db() as conn:
            df = pd.read_sql(f"SELECT * FROM appointments WHERE doctor='{name}'", conn)
        st.dataframe(df)

    # ================= STAFF =================

    elif role in ["Receptionist","Staff"]:
        st.title("Hospital Staff View")
        st.info("Limited access panel")
