import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, timedelta, time

# ==========================================================
# GLOBAL DATABASE CONNECTION (NO LOCK ISSUE)
# ==========================================================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("medivista.db", check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_connection()
c = conn.cursor()

# ==========================================================
# INITIALIZE DATABASE
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
# UI DESIGN
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
# LOGIN / REGISTER
# ==========================================================

if st.session_state.user is None:

    st.title("🏥 MediVista Hospital Portal")

    mode = st.radio("Select Option", ["Login", "Register"], horizontal=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Register":
        role = st.selectbox("Role", ["Patient"])

        if st.button("Register"):
            try:
                c.execute("INSERT INTO users VALUES (?,?,?,?)",
                          (email, hash_password(password), role, email))
                conn.commit()
                st.success("Registered Successfully")
            except sqlite3.IntegrityError:
                st.warning("User already exists")

    if mode == "Login":
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE email=? AND password=?",
                      (email, hash_password(password)))
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
            ["Dashboard","Doctors","Rooms","Staff Registration","Reports","Queries"])

        # ---------------- DASHBOARD ----------------
        if page == "Dashboard":
            st.title("Hospital Analytics Dashboard")

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
                chart = df_appointments.groupby("date")["amount"].sum().reset_index()
                fig = px.bar(chart, x="date", y="amount", title="Daily Revenue")
                st.plotly_chart(fig, use_container_width=True)

        # ---------------- DOCTOR MGMT ----------------
        elif page == "Doctors":

            st.title("Doctor Management")

            dname = st.text_input("Doctor Name")
            demail = st.text_input("Doctor Email (@hospitalstaff.com)")
            specialist = st.text_input("Specialist")
            nurse = st.text_input("Allotted Nurse")
            start = st.time_input("Start Time", time(8,0))
            end = st.time_input("End Time", time(18,0))

            if st.button("Add Doctor"):
                try:
                    c.execute("INSERT INTO doctors VALUES (NULL,?,?,?,?,?,?)",
                              (dname,demail,specialist,nurse,str(start),str(end)))
                    c.execute("INSERT INTO users VALUES (?,?,?,?)",
                              (demail,hash_password("Doctor@123"),"Doctor",dname))
                    conn.commit()
                    st.success("Doctor Added (Password: Doctor@123)")
                except:
                    st.warning("Doctor already exists")

            st.dataframe(pd.read_sql("SELECT * FROM doctors", conn))

        # ---------------- ROOMS ----------------
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

            st.dataframe(pd.read_sql("SELECT * FROM rooms", conn))

        # ---------------- STAFF REGISTRATION ----------------
        elif page == "Staff Registration":

            st.title("Register Receptionist / Staff")

            sname = st.text_input("Name")
            semail = st.text_input("Email (@hospitalstaff.com)")
            srole = st.selectbox("Role",["Receptionist","Staff"])

            if st.button("Register Staff"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?)",
                              (semail,hash_password("Staff@123"),srole,sname))
                    conn.commit()
                    st.success("Registered (Password: Staff@123)")
                except:
                    st.warning("Already registered")

        # ---------------- REPORT ----------------
        elif page == "Reports":
            st.title("Daily Revenue Report")
            today = datetime.now().strftime("%Y-%m-%d")
            df = pd.read_sql(f"SELECT * FROM appointments WHERE date='{today}'",conn)
            st.write(f"Today's Revenue: ₹ {df['amount'].sum() if not df.empty else 0}")
            st.dataframe(df)

        # ---------------- QUERIES ----------------
        elif page == "Queries":
            st.title("Patient Queries")
            st.dataframe(pd.read_sql("SELECT * FROM queries", conn))

    # ======================================================
    # DOCTOR PANEL
    # ======================================================

    elif role == "Doctor":
        st.title("Doctor Dashboard")

        df = pd.read_sql(f"SELECT * FROM appointments WHERE doctor='{name}'", conn)
        st.subheader("My Bookings")
        st.dataframe(df)

        st.subheader("Queries")
        st.dataframe(pd.read_sql("SELECT * FROM queries WHERE target='Doctor'", conn))

    # ======================================================
    # RECEPTIONIST PANEL
    # ======================================================

    elif role == "Receptionist":

        st.title("Receptionist Panel")

        st.subheader("Register Patient")

        pname = st.text_input("Name")
        pemail = st.text_input("Email")
        blood = st.selectbox("Blood Group",
                             ["A+","A-","B+","B-","O+","O-","AB+","AB-"])

        if st.button("Register Patient"):
            c.execute("INSERT INTO patients VALUES (NULL,?,?,?)",
                      (pname,pemail,blood))
            conn.commit()
            st.success("Patient Registered")

        st.subheader("Book Appointment")

        doctors = pd.read_sql("SELECT * FROM doctors", conn)
        rooms = pd.read_sql("SELECT * FROM rooms WHERE status='Available'", conn)

        if not doctors.empty:
            doctor = st.selectbox("Doctor", doctors["name"])
            date = st.date_input("Date")
            amount = st.number_input("Amount")

            doc = doctors[doctors["name"]==doctor].iloc[0]
            slots = generate_slots(
                datetime.strptime(doc["start_time"],"%H:%M:%S").time(),
                datetime.strptime(doc["end_time"],"%H:%M:%S").time()
            )

            slot = st.selectbox("Slot (20 mins)", slots)
            room = st.selectbox("Room", rooms["room_name"]) if not rooms.empty else None

            if st.button("Book"):
                c.execute("INSERT INTO appointments VALUES (NULL,?,?,?,?,?,?)",
                          (pname,doctor,slot,str(date),amount,room))
                c.execute("UPDATE rooms SET status='Occupied' WHERE room_name=?",(room,))
                conn.commit()
                st.success("Appointment Booked")

    # ======================================================
    # STAFF VIEW
    # ======================================================

    elif role == "Staff":
        st.title("Hospital Staff View")
        st.dataframe(pd.read_sql("SELECT name,nurse,start_time,end_time FROM doctors",conn))

    # ======================================================
    # PATIENT PANEL
    # ======================================================

    elif role == "Patient":

        st.title("Patient Portal")

        target = st.selectbox("Send Query To",["Admin","Doctor"])
        msg = st.text_area("Message")

        if st.button("Send Query"):
            c.execute("INSERT INTO queries VALUES (NULL,?,?,?)",
                      (name,target,msg))
            conn.commit()
            st.success("Query Sent")
