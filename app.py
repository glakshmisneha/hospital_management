import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, timedelta, time

# ==========================================================
# DATABASE CONNECTION (SAFE)
# ==========================================================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("medivista.db", check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_connection()
c = conn.cursor()

# ==========================================================
# INIT DATABASE
# ==========================================================

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

    c.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT,
        doctor TEXT,
        slot TEXT,
        date TEXT,
        amount REAL,
        room TEXT,
        room_amount REAL
    )
    """)

    # DEFAULT ADMIN
    c.execute("""
    INSERT OR IGNORE INTO users
    VALUES ('admin@admin.com',
            ?,
            'Admin',
            'Super Admin')
    """, (hashlib.sha256("Admin@123".encode()).hexdigest(),))

    conn.commit()

init_db()

# ==========================================================
# UTILITIES
# ==========================================================

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

# ==========================================================
# UI STYLE
# ==========================================================

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

# ==========================================================
# SESSION
# ==========================================================

if "user" not in st.session_state:
    st.session_state.user = None

# ==========================================================
# LOGIN
# ==========================================================

if st.session_state.user is None:

    st.title("🏥 MediVista Portal")

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
                st.warning("User exists")

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

# ==========================================================
# MAIN SYSTEM
# ==========================================================

else:

    role = st.session_state.user[2]
    name = st.session_state.user[3]

    st.sidebar.title("MediVista Admin")
    st.sidebar.write(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # ======================================================
    # ADMIN PANEL
    # ======================================================

    if role == "Admin":

        page = st.sidebar.radio("Navigation",
                                ["Dashboard","Doctors","Nurse Shifts","Rooms"])

        if page == "Dashboard":
            st.title("Hospital Analytics")

            df = pd.read_sql("SELECT * FROM appointments",conn)
            revenue = df["amount"].sum() + df["room_amount"].sum() if not df.empty else 0

            col1,col2 = st.columns(2)
            col1.metric("Total Revenue", f"₹ {revenue}")
            col2.metric("Total Visits", len(df))

        elif page == "Doctors":

            st.title("Add Doctor Shift")

            dname = st.text_input("Doctor Name")
            demail = st.text_input("Email (@hospitalstaff.com)")
            specialist = st.text_input("Specialist")
            nurse = st.text_input("Allocated Nurse")
            start = st.time_input("Shift Start", time(8,0))
            end = st.time_input("Shift End", time(18,0))

            if st.button("Add Doctor"):
                try:
                    c.execute("INSERT INTO doctors VALUES (NULL,?,?,?,?,?,?)",
                              (dname,demail,specialist,nurse,str(start),str(end)))
                    c.execute("INSERT INTO users VALUES (?,?,?,?)",
                              (demail,hash_password("Doctor@123"),"Doctor",dname))
                    conn.commit()
                    st.success("Doctor Added")
                except:
                    st.warning("Doctor exists")

            st.dataframe(pd.read_sql("SELECT * FROM doctors",conn))

        elif page == "Nurse Shifts":

            st.title("Add Nurse Shift")

            nname = st.text_input("Nurse Name")
            shift_start = st.time_input("Shift Start")
            shift_end = st.time_input("Shift End")
            allocated_doc = st.text_input("Allocated Doctor")

            if st.button("Add Nurse"):
                c.execute("INSERT INTO nurses VALUES (NULL,?,?,?,?)",
                          (nname,str(shift_start),str(shift_end),allocated_doc))
                conn.commit()
                st.success("Nurse Shift Added")

            st.dataframe(pd.read_sql("SELECT * FROM nurses",conn))

        elif page == "Rooms":

            st.title("Room Management")

            room = st.text_input("Room Name")
            rtype = st.selectbox("Room Type",["ICU","General","Private"])
            status = st.selectbox("Status",["Available","Occupied"])

            if st.button("Add Room"):
                try:
                    c.execute("INSERT INTO rooms VALUES (NULL,?,?,?)",
                              (room,rtype,status))
                    conn.commit()
                    st.success("Room Added")
                except:
                    st.warning("Room exists")

            st.dataframe(pd.read_sql("SELECT * FROM rooms",conn))

    # ======================================================
    # RECEPTIONIST PANEL (WITH LEFT OPTIONS)
    # ======================================================

    elif role == "Receptionist":

        page = st.sidebar.radio("Receptionist Options",
                                ["Patient Details",
                                 "Register Patient",
                                 "Book Appointment",
                                 "Room Booking"])

        if page == "Patient Details":
            st.title("All Patients")
            st.dataframe(pd.read_sql("SELECT * FROM patients",conn))

        elif page == "Register Patient":
            st.title("Register Patient")

            pname = st.text_input("Name")
            pemail = st.text_input("Email")
            blood = st.selectbox("Blood Group",
                                 ["A+","A-","B+","B-","O+","O-","AB+","AB-"])

            if st.button("Register"):
                c.execute("INSERT INTO patients VALUES (NULL,?,?,?)",
                          (pname,pemail,blood))
                conn.commit()
                st.success("Patient Registered")

        elif page == "Book Appointment":

            st.title("Book Appointment")

            doctors = pd.read_sql("SELECT * FROM doctors",conn)
            patients = pd.read_sql("SELECT * FROM patients",conn)

            if not doctors.empty and not patients.empty:

                doctor = st.selectbox("Doctor", doctors["name"])
                patient = st.selectbox("Patient", patients["name"])
                date = st.date_input("Date")
                amount = st.number_input("Appointment Payment")

                doc = doctors[doctors["name"]==doctor].iloc[0]
                slots = generate_slots(
                    datetime.strptime(doc["start_time"],"%H:%M:%S").time(),
                    datetime.strptime(doc["end_time"],"%H:%M:%S").time()
                )

                slot = st.selectbox("20-Min Slot", slots)

                if st.button("Confirm Booking"):
                    c.execute("""
                    INSERT INTO appointments
                    VALUES (NULL,?,?,?,?,?,?,?)
                    """,(patient,doctor,slot,str(date),amount,None,0))
                    conn.commit()
                    st.success("Appointment Booked")

        elif page == "Room Booking":

            st.title("Room Booking")

            rooms = pd.read_sql("SELECT * FROM rooms WHERE status='Available'",conn)
            patients = pd.read_sql("SELECT * FROM patients",conn)

            if not rooms.empty and not patients.empty:

                room = st.selectbox("Room", rooms["room_name"])
                patient = st.selectbox("Patient", patients["name"])
                room_amount = st.number_input("Room Payment")

                if st.button("Book Room"):
                    c.execute("""
                    INSERT INTO appointments
                    VALUES (NULL,?,?,?,?,?,?,?)
                    """,(patient,None,None,str(datetime.now().date()),0,room,room_amount))

                    c.execute("UPDATE rooms SET status='Occupied' WHERE room_name=?",(room,))
                    conn.commit()
                    st.success("Room Booked")

    # ======================================================
    # DOCTOR PANEL
    # ======================================================

    elif role == "Doctor":
        st.title("Doctor Panel")
        st.dataframe(pd.read_sql(f"SELECT * FROM appointments WHERE doctor='{name}'",conn))

    # ======================================================
    # STAFF PANEL
    # ======================================================

    elif role == "Staff":
        st.title("Staff View")
        st.dataframe(pd.read_sql("SELECT * FROM nurses",conn))
