import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, timedelta, time

# =====================================================
# DATABASE CONNECTION (SAFE - NO LOCK)
# =====================================================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("medivista.db", check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_connection()
c = conn.cursor()

# =====================================================
# DATABASE INITIALIZATION
# =====================================================

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
        amount REAL DEFAULT 0,
        room TEXT DEFAULT '',
        room_amount REAL DEFAULT 0
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

# =====================================================
# UTILITIES
# =====================================================

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

# =====================================================
# UI DESIGN
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
                st.success("Registered Successfully")
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

# =====================================================
# MAIN SYSTEM
# =====================================================

else:

    role = st.session_state.user[2]
    name = st.session_state.user[3]

    st.sidebar.title("MediVista")
    st.sidebar.write(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # =====================================================
    # ADMIN PANEL
    # =====================================================

    if role == "Admin":

        page = st.sidebar.radio("Navigation",
            ["Dashboard","Doctors","Nurses","Rooms","Staff Registration","Queries"])

        # -------- DASHBOARD --------
        if page == "Dashboard":

            st.title("Hospital Analytics Dashboard")

            df = pd.read_sql("SELECT * FROM appointments", conn)
            df_doc = pd.read_sql("SELECT * FROM doctors", conn)
            df_pat = pd.read_sql("SELECT * FROM patients", conn)

            revenue = df["amount"].sum() + df["room_amount"].sum() if not df.empty else 0

            col1,col2,col3,col4 = st.columns(4)
            col1.metric("Total Revenue", f"₹ {revenue}")
            col2.metric("Total Patients", len(df_pat))
            col3.metric("Total Doctors", len(df_doc))
            col4.metric("Total Visits", len(df))

            if not df.empty:
                chart = df.groupby("date")[["amount","room_amount"]].sum().reset_index()
                chart["total"] = chart["amount"] + chart["room_amount"]
                fig = px.bar(chart, x="date", y="total", title="Daily Revenue")
                st.plotly_chart(fig, use_container_width=True)

        # -------- DOCTOR MANAGEMENT --------
        elif page == "Doctors":

            st.title("Add Doctor Shift")

            dname = st.text_input("Doctor Name")
            demail = st.text_input("Doctor Email")
            specialist = st.text_input("Specialist")
            nurse = st.text_input("Allocated Nurse")
            start = st.time_input("Shift Start", time(8,0))
            end = st.time_input("Shift End", time(18,0))

            if st.button("Add Doctor"):
                try:
                    c.execute("""
                    INSERT INTO doctors
                    (name,email,specialist,nurse,start_time,end_time)
                    VALUES (?,?,?,?,?,?)
                    """,(dname,demail,specialist,nurse,str(start),str(end)))

                    c.execute("INSERT INTO users VALUES (?,?,?,?)",
                              (demail,hash_password("Doctor@123"),"Doctor",dname))

                    conn.commit()
                    st.success("Doctor Added (Password: Doctor@123)")
                except:
                    st.warning("Doctor already exists")

            st.dataframe(pd.read_sql("SELECT * FROM doctors",conn))

        # -------- NURSES --------
        elif page == "Nurses":

            st.title("Add Nurse Shift")

            nname = st.text_input("Nurse Name")
            shift_start = st.time_input("Shift Start")
            shift_end = st.time_input("Shift End")
            allocated_doc = st.text_input("Allocated Doctor")

            if st.button("Add Nurse"):
                c.execute("""
                INSERT INTO nurses
                (name,shift_start,shift_end,allocated_doctor)
                VALUES (?,?,?,?)
                """,(nname,str(shift_start),str(shift_end),allocated_doc))
                conn.commit()
                st.success("Nurse Added")

            st.dataframe(pd.read_sql("SELECT * FROM nurses",conn))

        # -------- ROOMS --------
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
                    st.warning("Room already exists")

            st.subheader("Edit Room Availability")

            rooms = pd.read_sql("SELECT * FROM rooms",conn)

            if not rooms.empty:
                selected = st.selectbox("Select Room", rooms["room_name"])
                new_status = st.selectbox("Change Status",["Available","Occupied"])

                if st.button("Update Status"):
                    c.execute("UPDATE rooms SET status=? WHERE room_name=?",
                              (new_status,selected))
                    conn.commit()
                    st.success("Updated")

            st.dataframe(rooms)

        # -------- STAFF REGISTRATION --------
        elif page == "Staff Registration":

            st.title("Register Receptionist / Staff")

            sname = st.text_input("Name")
            semail = st.text_input("Email")
            srole = st.selectbox("Role",["Receptionist","Staff"])

            if st.button("Register Staff"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?)",
                              (semail,hash_password("Staff@123"),srole,sname))
                    conn.commit()
                    st.success("Registered (Password: Staff@123)")
                except:
                    st.warning("Already registered")

        # -------- QUERIES --------
        elif page == "Queries":
            st.title("Patient Queries")
            st.dataframe(pd.read_sql("SELECT * FROM queries",conn))

    # =====================================================
    # DOCTOR PANEL
    # =====================================================

    elif role == "Doctor":
        st.title("Doctor Dashboard")
        st.dataframe(pd.read_sql(f"SELECT * FROM appointments WHERE doctor='{name}'",conn))

    # =====================================================
    # RECEPTIONIST PANEL
    # =====================================================

    elif role == "Receptionist":

        page = st.sidebar.radio("Receptionist Options",
                                ["Patient Details",
                                 "Register Patient",
                                 "Book Appointment",
                                 "Room Booking"])

        if page == "Patient Details":
            st.dataframe(pd.read_sql("SELECT * FROM patients",conn))

        elif page == "Register Patient":

            pname = st.text_input("Name")
            pemail = st.text_input("Email")
            blood = st.selectbox("Blood Group",
                                 ["A+","A-","B+","B-","O+","O-","AB+","AB-"])

            if st.button("Register"):
                c.execute("INSERT INTO patients VALUES (NULL,?,?,?)",
                          (pname,pemail,blood))
                conn.commit()
                st.success("Registered")

        elif page == "Book Appointment":

            doctors = pd.read_sql("SELECT * FROM doctors",conn)
            patients = pd.read_sql("SELECT * FROM patients",conn)

            if not doctors.empty and not patients.empty:

                doctor = st.selectbox("Doctor", doctors["name"])
                patient = st.selectbox("Patient", patients["name"])
                date = st.date_input("Date")
                amount = st.number_input("Appointment Payment")

                doc = doctors.iloc[0]
                slots = generate_slots(time(8,0), time(18,0))
                slot = st.selectbox("20-min Slot", slots)

                if st.button("Confirm Booking"):
                    c.execute("""
                    INSERT INTO appointments
                    (patient,doctor,slot,date,amount,room,room_amount)
                    VALUES (?,?,?,?,?,?,?)
                    """,(patient,doctor,slot,str(date),amount,"",0))
                    conn.commit()
                    st.success("Appointment Booked")

        elif page == "Room Booking":

            rooms = pd.read_sql("SELECT * FROM rooms WHERE status='Available'",conn)
            patients = pd.read_sql("SELECT * FROM patients",conn)

            if not rooms.empty and not patients.empty:

                room = st.selectbox("Room", rooms["room_name"])
                patient = st.selectbox("Patient", patients["name"])
                room_amount = st.number_input("Room Payment")

                if st.button("Book Room"):
                    c.execute("""
                    INSERT INTO appointments
                    (patient,doctor,slot,date,amount,room,room_amount)
                    VALUES (?,?,?,?,?,?,?)
                    """,(patient,"","",str(datetime.now().date()),0,room,room_amount))
                    c.execute("UPDATE rooms SET status='Occupied' WHERE room_name=?",(room,))
                    conn.commit()
                    st.success("Room Booked")
